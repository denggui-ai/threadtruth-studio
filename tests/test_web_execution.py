"""One-call web envelopes bind actual unchanged exports; no external execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image


ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'skills/threadtruth-studio/scripts/web-task.py'
spec=importlib.util.spec_from_file_location('web_execution_task',SCRIPT)
task=importlib.util.module_from_spec(spec);spec.loader.exec_module(task)
spec=importlib.util.spec_from_file_location('web_execution_library',SCRIPT.with_name('visual_library.py'))
library=importlib.util.module_from_spec(spec);spec.loader.exec_module(library)


class WebExecutionTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve();self.job=self.root/'task'
        self.source=self.root/'garment.png';Image.new('RGB',(20,30),'red').save(self.source)
        self.context=dict(outfit='synthetic',style='ecommerce-studio',mode='C',output_form='flat-lay',
                          size=[20,30],first_pose=1,canvas_policy='ratio-first')

    def create(self,*,route='chatgpt_web',schema=2,preview=False,visual=False):
        context=dict(self.context)
        if preview:context['purpose']='preview-grid'
        args=dict(schema_version=schema)
        if schema==2:args.update(context=context,route=route)
        prompts=['Keep the red garment and its visible construction.\n服饰原色保持。\n']
        if visual:
            visual_plan=library.prepare(dict(entry_id='ecommerce-studio',count=1,first_pose=1,
                output_form='flat-lay',objective='product-display',
                garment=dict(description='Synthetic red garment.',keep=['original red color'],
                             source_sha256s=[task.digest(self.source)]),
                inventory=[dict(sha256=task.digest(self.source),role='garment-source')]))
            args.update(visual_plan=visual_plan,count=1);prompts=None
        task.create(self.job,[self.source],prompts,[20,30],identity=False,**args)
        task.export(self.job)
        data=task.read(self.job);self.handoff=task.handoff_directory(self.job,data,data['looks'][0])
        return data

    def before(self):
        return {str(p.relative_to(self.job)):p.read_bytes() for p in self.job.rglob('*') if p.is_file()}

    def assert_preserved(self,before):
        for name,raw in before.items():self.assertEqual((self.job/name).read_bytes(),raw,name)

    def prepare(self):return task.export_web_execution(self.job,1)

    def reserve(self,packet,**overrides):
        data=task.read(self.job)
        args=dict(look=1,ready=True,refs=task.reference_hashes(self.job,1),
            conversation='https://chatgpt.com/c/synthetic-envelope',
            expected_plan_sha256=task.plan_fingerprint(data),
            expected_prompt_sha256=data['looks'][0]['prompt_sha256'],
            execution_manifest=packet['execution_manifest'],
            expected_submission_sha256=packet['submission_sha256'])
        args.update(overrides);return task.update(self.job,'reserve',**args)

    def authorize(self):
        task.update(self.job,'authorize',limit=1,note='Synthetic one-request authority; no external call')

    def test_explicit_envelope_preserves_every_existing_byte_and_authority(self):
        data=self.create(visual=True);before=self.before();packet=self.prepare()
        self.assert_preserved(before)
        self.assertEqual(task.read(self.job),data)
        metadata=json.loads(Path(packet['execution_manifest']).read_text())
        canonical=(self.handoff/'prompt.txt').read_bytes()
        message=Path(packet['submission_file']).read_bytes();helper=task.web_execution_helper()
        self.assertEqual(message,helper.PREFIX+canonical+helper.SUFFIX)
        self.assertEqual(metadata['canonical_prompt']['sha256'],hashlib.sha256(canonical).hexdigest())
        self.assertEqual(metadata['canonical_manifest']['sha256'],task.digest(self.handoff/'manifest.json'))
        self.assertEqual(metadata['submission']['sha256'],hashlib.sha256(message).hexdigest())
        self.assertEqual(metadata['image_tool_call_limit'],1)
        self.assertEqual(metadata['attachments'][0]['sha256'],task.digest(self.source))
        self.assertIsNone(data['authorization']);self.assertEqual(data['attempts'],0)
        complete=self.before();self.assertEqual(self.prepare(),packet);self.assert_preserved(complete)

    def test_web_and_native_canonical_art_remain_identical_and_reexport_unchanged(self):
        self.create(visual=True);web=(self.handoff/'prompt.txt').read_bytes()
        self.prepare();before=self.before();task.export(self.job);self.assert_preserved(before)
        self.job=self.root/'native';self.create(route='codex_native',visual=True)
        native=(self.handoff/'prompt.txt').read_bytes();before=self.before()
        self.assertEqual(web,native)
        request=json.loads((self.handoff/'request.json').read_text())
        self.assertEqual(request['prompt'].encode(),native)
        with self.assertRaisesRegex(ValueError,'web only'):self.prepare()
        task.export(self.job);self.assert_preserved(before)

    def test_legacy_schema1_keeps_exact_prompt_and_no_manifest(self):
        self.create(schema=1);before=self.before();packet=self.prepare()
        self.assert_preserved(before)
        self.assertIsNone(json.loads(Path(packet['execution_manifest']).read_text())['canonical_manifest'])
        self.assertFalse((self.handoff/'manifest.json').exists())
        self.authorize();data=self.reserve(packet);task.check_evidence(self.job,data)
        self.assertEqual(data['attempts'],1)

    def test_preview_envelope_still_wraps_one_complete_six_panel_request(self):
        self.create(preview=True);before=self.before();packet=self.prepare()
        self.assert_preserved(before)
        message=Path(packet['submission_file']).read_text()
        self.assertIn('One six-panel direction preview',message)
        self.assertIn('QA belongs to the caller',message)
        self.assertEqual(json.loads(Path(packet['execution_manifest']).read_text())['image_tool_call_limit'],1)

    def test_changed_prompt_rejected_even_if_manifest_hash_was_recomputed(self):
        self.create();path=self.handoff/'prompt.txt';path.write_bytes(path.read_bytes()+b'Alter garment.')
        manifest=self.handoff/'manifest.json';value=json.loads(manifest.read_text())
        value['tool_prompt_sha256']=task.digest(path);manifest.write_text(json.dumps(value,ensure_ascii=False,indent=2))
        before=self.before()
        with self.assertRaisesRegex(ValueError,'Canonical handoff changed'):self.prepare()
        self.assert_preserved(before);self.assertFalse((self.handoff/'web-execution-v1').exists())

    def test_changed_manifest_fields_or_bytes_fail_without_rewriting(self):
        self.create();path=self.handoff/'manifest.json';original=path.read_bytes()
        for change in ('current_plan_sha256','frozen_prompt_sha256','reference_hashes','whitespace'):
            with self.subTest(change=change):
                value=json.loads(original)
                if change=='whitespace':raw=original+b'\n'
                else:
                    value[change]=[] if change=='reference_hashes' else '0'*64
                    raw=json.dumps(value,ensure_ascii=False,indent=2).encode()
                path.write_bytes(raw);before=self.before()
                with self.assertRaisesRegex(ValueError,'Canonical handoff changed'):self.prepare()
                self.assert_preserved(before)
        path.write_bytes(original)

    def test_immutable_package_tampering_blocks_preparation_and_reservation(self):
        self.create();packet=self.prepare();self.authorize()
        for key in ('submission_file','execution_manifest'):
            with self.subTest(key=key):
                path=Path(packet[key]);original=path.read_bytes();path.write_bytes(original+b' ');before=self.before()
                with self.assertRaisesRegex(ValueError,'execution package changed'):self.prepare()
                with self.assertRaisesRegex(ValueError,'execution package changed'):self.reserve(packet)
                self.assert_preserved(before);self.assertEqual(task.read(self.job)['attempts'],0)
                path.write_bytes(original)

    def test_attachment_tampering_blocks_prepare_and_reserve(self):
        self.create();packet=self.prepare();self.authorize()
        attachment=next(self.handoff.glob('01-*'));attachment.write_bytes(b'changed');before=self.before()
        for action in (self.prepare,lambda:self.reserve(packet)):
            with self.assertRaisesRegex(ValueError,'attachment changed'):action()
        self.assert_preserved(before);self.assertEqual(task.read(self.job)['attempts'],0)

    def test_stale_envelope_after_pending_revision_cannot_reserve(self):
        self.create();old=self.prepare();old_bytes=self.before();self.authorize()
        task.update(self.job,'revise-pending',look=1,note='Change only scene',prompt='Same red garment in a new room.',
                    expected_prompt_sha256=task.read(self.job)['looks'][0]['prompt_sha256'])
        task.export(self.job)
        with self.assertRaisesRegex(ValueError,'exact current web execution'):self.reserve(old)
        self.assertEqual(task.read(self.job)['attempts'],0)
        for key in ('submission_file','execution_manifest'):
            path=Path(old[key]);self.assertEqual(path.read_bytes(),old_bytes[str(path.relative_to(self.job))])
        current=self.prepare();data=self.reserve(current);self.assertEqual(data['attempts'],1)

    def test_reservation_binds_exact_submission_then_unknown_blocks_another_call(self):
        self.create();packet=self.prepare();self.authorize();before=self.before()
        with self.assertRaisesRegex(ValueError,'exact current web execution'):
            self.reserve(packet,expected_submission_sha256='0'*64)
        self.assert_preserved(before)
        data=self.reserve(packet);record=data['looks'][0]['web_execution']
        self.assertEqual(record['sha256'],task.digest(Path(packet['execution_manifest'])))
        task.check_evidence(self.job,data)
        task.update(self.job,'unknown',look=1)
        with self.assertRaises(ValueError):self.reserve(packet)
        with self.assertRaises(ValueError):self.prepare()
        self.assertEqual(task.read(self.job)['attempts'],1)

    def test_reserved_artifacts_are_checked_by_existing_evidence_gate(self):
        self.create();packet=self.prepare();self.authorize();data=self.reserve(packet)
        path=Path(packet['submission_file']);path.write_bytes(path.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'Retained web execution artifact changed'):
            task.check_evidence(self.job,data)
        before=(self.job/'task.json').read_bytes()
        with self.assertRaises(ValueError):task.update(self.job,'unknown',look=1)
        self.assertEqual((self.job/'task.json').read_bytes(),before)

    def test_prepared_execution_cannot_be_silently_omitted_from_reservation(self):
        self.create();packet=self.prepare();self.authorize();before=self.before()
        with self.assertRaisesRegex(ValueError,'requires its manifest and submission hash binding'):
            self.reserve(packet,execution_manifest=None,expected_submission_sha256=None)
        self.assert_preserved(before);self.assertEqual(task.read(self.job)['attempts'],0)

    def test_retry_retains_old_execution_and_requires_a_new_attempt_envelope(self):
        self.create();first=self.prepare();self.authorize();self.reserve(first)
        result=self.root/'result.png';Image.new('RGB',(20,30),'blue').save(result)
        task.update(self.job,'returned',look=1,file=result)
        task.update(self.job,'reject',look=1,note='Synthetic wrong garment color')
        task.update(self.job,'retry-authorize',look=1,expected_attempt=1,approval_id='synthetic-retry',
                    note='Synthetic explicit retry authority',prompt='Retain the original red garment.')
        data=task.read(self.job);task.check_evidence(self.job,data)
        self.assertIn('web_execution',data['looks'][0]['history'][0])
        self.assertNotIn('web_execution',data['looks'][0]);self.assertEqual(data['attempts'],1)
        task.export(self.job)
        with self.assertRaisesRegex(ValueError,'exact current web execution'):self.reserve(first)
        second=self.prepare();self.assertNotEqual(first['execution_manifest'],second['execution_manifest'])
        data=self.reserve(second);task.check_evidence(self.job,data);self.assertEqual(data['attempts'],2)

    def test_cli_exports_and_binds_without_changing_canonical_files(self):
        self.create();before=self.before()
        result=subprocess.run([sys.executable,str(SCRIPT),'export-web-execution','--task',str(self.job),'--look','1'],
                              capture_output=True,text=True,check=True)
        packet=json.loads(result.stdout);self.assert_preserved(before);self.authorize()
        data=task.read(self.job)
        args=[sys.executable,str(SCRIPT),'reserve','--task',str(self.job),'--look','1','--ready',
              '--refs',task.digest(self.source),'--conversation','https://chatgpt.com/c/synthetic-cli',
              '--expected-plan-sha256',task.plan_fingerprint(data),
              '--execution-manifest',packet['execution_manifest'],
              '--expected-submission-sha256',packet['submission_sha256']]
        result=subprocess.run(args,capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(result.stdout)['attempts'],1)


class WebExecutionV2Tests(unittest.TestCase):
    def test_nine_preview_envelope_reserves_and_retains_history_without_rebuilding(self):
        from tests import test_nine_task as fixtures
        case=fixtures.NineTaskTests();case.setUp();self.addCleanup(case.doCleanups)
        backend=fixtures.task
        data=case.create(preview=True,route='chatgpt_web')
        backend.export(case.job)
        packet=backend.export_web_execution(case.job,1)
        helper=backend.web_execution_helper()
        meta=json.loads(Path(packet['execution_manifest']).read_bytes())
        submission=Path(packet['submission_file']).read_bytes()
        self.assertEqual(meta['schema_version'],2)
        self.assertEqual(Path(packet['execution_manifest']).parent.name,'web-execution-v2')
        self.assertIn(b'A multi-panel direction preview',submission)
        self.assertIn(b'One nine-panel 3x3 direction preview',submission)
        self.assertNotIn(b'A six-panel direction preview',submission)
        self.assertEqual(meta['image_tool_call_limit'],1)
        canonical=(case.job/meta['canonical_prompt']['file']).read_bytes()
        self.assertEqual(submission,helper.PREFIX_V2+canonical+helper.SUFFIX)
        retained={key:Path(packet[key]).read_bytes() for key in ('execution_manifest','submission_file')}
        backend.update(case.job,'authorize',limit=1,note='Synthetic one-preview request authority.')
        args=dict(look=1,ready=True,refs=backend.reference_hashes(case.job,1),
                  conversation='https://chatgpt.com/c/synthetic-nine-envelope',
                  expected_plan_sha256=backend.plan_fingerprint(data),
                  expected_prompt_sha256=data['looks'][0]['prompt_sha256'])
        with self.assertRaisesRegex(ValueError,'requires its manifest and submission hash binding'):
            backend.update(case.job,'reserve',**args)
        data=backend.update(case.job,'reserve',**args,execution_manifest=packet['execution_manifest'],
                            expected_submission_sha256=packet['submission_sha256'])
        self.assertEqual(data['attempts'],1)
        backend.update(case.job,'returned',look=1,file=case.image('envelope-result','gray'))
        backend.update(case.job,'reject',look=1,note='Synthetic rejected preview, no visual assertion.')
        data=backend.update(case.job,'retry-authorize',look=1,expected_attempt=1,approval_id='nine-envelope-retry',
            note='Synthetic explicit second request authority.',prompt=data['looks'][0]['prompt'])
        historical=data['looks'][0]['history'][0]
        helper.check_retained(case.job,historical)
        backend.check_evidence(case.job,data)
        for key,raw in retained.items():self.assertEqual(Path(packet[key]).read_bytes(),raw)
        self.assertNotIn('web_execution',data['looks'][0])
        self.assertEqual(data['looks'][0]['attempt_number'],2)
        self.assertEqual(data['attempts'],1)
        backend.export(case.job)
        next_packet=backend.export_web_execution(case.job,1)
        self.assertNotEqual(next_packet['execution_manifest'],packet['execution_manifest'])
        helper.check_retained(case.job,historical)


if __name__=='__main__':unittest.main()
