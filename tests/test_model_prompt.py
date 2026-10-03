import importlib.util
from pathlib import Path
import unittest
import copy
import tempfile
from unittest.mock import patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('model_prompt',ROOT/'tools/style_preview.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class ModelPromptTests(unittest.TestCase):
    def setUp(self):
        self.plan=m._plan_v5(ROOT,'model-prompt-test','beige-blazer-denim-outfit')
        self.preview=next(p for p in self.plan['previews'] if p['style']=='korean-cold-editorial')
        self.model=dict(source_type='new',scope='full',subject='adult male model',
                        locked=['apparent age around 40','natural fuller proportions'],adjustable=['friendly smile'],consent_note='')

    def test_native_prompt_rejects_overfull_actual_attachment_list_before_writing(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            refs=[]
            for i,color in enumerate(['blue','green','yellow','purple','orange']):
                path=Path(tmp)/f'{i}.png';Image.new('RGB',(20,30),color).save(path)
                refs.append(dict(path=str(path),role='aesthetic-reference',sha256=m.digest(path.read_bytes())))
            with patch.object(m,'run_dir',return_value=Path(tmp)/'run'):
                with self.assertRaisesRegex(ValueError,'reference'):
                    m.single_prompt(ROOT,'native-limit-test','ecommerce-studio',1,'beige-blazer-denim-outfit',model=self.model,model_references=refs)
            self.assertFalse((Path(tmp)/'run').exists())

    def test_custom_casting_reaches_preview_and_single_without_demo_anchor(self):
        general, full=m._final_negatives(ROOT)
        _,negative=m._canonical_action_zero(ROOT)
        for text in [m._prompt(self.preview,self.plan['source'],self.plan['identity_anchor'],negative,m._head_gaze_guidance(ROOT),model=self.model,model_references=[]),
                     m._single_prompt(self.preview,self.plan['source'],self.plan['identity_anchor'],self.preview['poses'][0],general,full,'2:3',False,m._head_gaze_guidance(ROOT),model=self.model,model_references=[])]:
            self.assertIn('adult male model',text)
            self.assertIn('natural fuller proportions',text)
            self.assertIn('friendly smile',text)
            self.assertNotIn('one adult female model',text)
            self.assertNotIn(self.plan['identity_anchor']['path'],text)
            self.assertNotIn('Attitude: calm, detached',text)

    def test_custom_model_filters_declared_expression_and_retains_other_mood_details(self):
        general,full=m._final_negatives(ROOT);_,negative=m._canonical_action_zero(ROOT)
        for text in [m._prompt(self.preview,self.plan['source'],self.plan['identity_anchor'],negative,m._head_gaze_guidance(ROOT),model=self.model),
                     m._single_prompt(self.preview,self.plan['source'],self.plan['identity_anchor'],self.preview['poses'][0],general,full,'2:3',False,m._head_gaze_guidance(ROOT),model=self.model)]:
            for old in ['detached expression','no fake commercial smile']:
                self.assertNotIn(old,text)
            for retained in ['dewy translucent makeup','natural flyaway hair','medium format film photography texture','realistic native skin texture']:
                self.assertIn(retained,text)
            self.assertIn('friendly smile',text)
            self.assertIn(self.preview['visual']['lighting'],text)
            self.assertIn('no excessive retouching',text)
            self.assertIn('restrained editorial mood',text)

    def test_existing_reference_has_identity_role_and_not_product_authority(self):
        self.model['source_type']='ai'
        refs=[dict(path='brand-face.png',role='identity-reference',sha256='a'*64)]
        _,negative=m._canonical_action_zero(ROOT)
        text=m._prompt(self.preview,self.plan['source'],self.plan['identity_anchor'],negative,m._head_gaze_guidance(ROOT),model=self.model,model_references=refs)
        self.assertIn('brand-face.png',text)
        self.assertIn('identity-reference',text)
        self.assertNotIn(self.plan['identity_anchor']['path'],text)


    def test_public_prompt_entry_returns_actual_ordered_attachments_and_checks_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            garment=root/'garment.png';face=root/'face.png'
            Image.new('RGB',(20,30),'red').save(garment);Image.new('RGB',(20,30),'blue').save(face)
            plan=copy.deepcopy(self.plan)
            plan['source']['assets']=[dict(path='garment.png',sha256=m.digest(garment.read_bytes()),role='outfit-source')]
            model=dict(self.model,source_type='ai')
            refs=[dict(path=str(face),role='identity-reference',sha256=m.digest(face.read_bytes()))]
            with patch.object(m,'_plan_v5',return_value=plan), patch.object(m,'_final_negatives',return_value=('no collage','no cropped shoes')), patch.object(m,'_head_gaze_guidance',return_value='natural head'):
                result=m.single_prompt(root,'model-test','korean-cold-editorial',1,'beige-blazer-denim-outfit','2:3',model=model,model_references=refs)
                self.assertEqual([r['role'] for r in result['references']], ['garment-source','identity-reference'])
                self.assertEqual(result['references'][1]['sha256'],refs[0]['sha256'])
                face.write_bytes(b'changed')
                with self.assertRaises(ValueError):m.single_prompt(root,'model-bad','korean-cold-editorial',1,'beige-blazer-denim-outfit',model=model,model_references=refs)

    def test_model_references_without_model_are_not_silently_ignored(self):
        with self.assertRaises(ValueError):m._apply_model(['prompt'],1,None,[dict(path='face.png',role='identity-reference')])

    def test_native_prompt_blocks_hash_matched_fake_attachments_before_writing(self):
        for broken_role in ('garment-source', 'identity-reference', 'aesthetic-reference'):
            with self.subTest(role=broken_role), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                garment = root/'garment.png'; reference = root/'person.png'
                Image.new('RGB', (20, 30), 'red').save(garment)
                Image.new('RGB', (20, 30), 'blue').save(reference)
                (garment if broken_role == 'garment-source' else reference).write_bytes(b'not an image')
                plan = copy.deepcopy(self.plan)
                plan['source']['assets'] = [dict(path='garment.png', sha256=m.digest(garment.read_bytes()), role='outfit-source')]
                role = 'aesthetic-reference' if broken_role == 'aesthetic-reference' else 'identity-reference'
                model = dict(self.model, source_type='new' if role == 'aesthetic-reference' else 'ai')
                refs = [dict(path=str(reference), sha256=m.digest(reference.read_bytes()), role=role)]
                with patch.object(m, '_plan_v5', return_value=plan), patch.object(m, '_final_negatives', return_value=('no collage', 'no crop')), patch.object(m, '_head_gaze_guidance', return_value='natural head'):
                    with self.assertRaisesRegex(ValueError, 'image|Image'):
                        m.single_prompt(root, 'bad-attachment', 'korean-cold-editorial', 1, 'beige-blazer-denim-outfit', model=model, model_references=refs)
                self.assertFalse(m.run_dir(root, 'bad-attachment').exists())

    def test_actual_prompt_and_attachments_keep_confirmed_supplement_role(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            paths=[]
            for name,color in [('garment','red'),('original','blue'),('accepted','green')]:
                p=root/(name+'.png');Image.new('RGB',(20,30),color).save(p);paths.append(p)
            plan=copy.deepcopy(self.plan)
            plan['source']['assets']=[dict(path='garment.png',sha256=m.digest(paths[0].read_bytes()),role='outfit-source')]
            refs=[dict(path=str(paths[1]),role='identity-reference',sha256=m.digest(paths[1].read_bytes())),
                  dict(path=str(paths[2]),role='model-supplement',sha256=m.digest(paths[2].read_bytes()),
                       scope='face',confirmation_note='User accepted this generated face')]
            with patch.object(m,'_plan_v5',return_value=plan),patch.object(m,'_final_negatives',return_value=('no collage','no crop')),patch.object(m,'_head_gaze_guidance',return_value='natural head'):
                try: result=m.single_prompt(root,'supplement','korean-cold-editorial',1,'beige-blazer-denim-outfit',model=dict(self.model,source_type='ai'),model_references=refs)
                except ValueError as error:self.fail('Confirmed supplement prompt entry is missing: '+str(error))
                self.assertEqual([r['role'] for r in result['references']],['garment-source','identity-reference','model-supplement'])
                self.assertEqual(result['references'][-1]['scope'],'face')
                self.assertEqual(result['references'][-1]['confirmation_note'],refs[-1]['confirmation_note'])
                text=(root/result['path']).read_text()
                self.assertIn('supplement',text)
                self.assertIn('original identity',text)
                self.assertIn('friendly smile',text)
                self.assertNotIn(self.plan['identity_anchor']['path'],text)
                refs[-1]['confirmation_note']=''
                with self.assertRaises(ValueError):m.single_prompt(root,'bad','korean-cold-editorial',1,'beige-blazer-denim-outfit',model=dict(self.model,source_type='ai'),model_references=refs)


if __name__=='__main__':unittest.main()
