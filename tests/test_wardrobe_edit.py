"""Meaningful deterministic image tests; generated images are synthetic fixtures."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1]/'skills/threadtruth-studio/scripts/wardrobe-edit.cjs'

class WardrobeEditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.run = self.root/'run'
        self.base = self.root/'base.png'; self.donor = self.root/'donor.png'; self.garment = self.root/'garment.png'
        Image.new('RGB',(64,96),(20,90,40)).save(self.base)
        Image.new('RGB',(64,96),(230,160,185)).save(self.donor)
        Image.new('RGB',(32,48),'pink').save(self.garment)
        self.spec = dict(base_path=str(self.base),base_sha256=hashlib.sha256(self.base.read_bytes()).hexdigest(),
                         garment_paths=[str(self.garment)],garment_conditions='Replace only upper sweater; retain the explicitly selected skirt.',size=[64,96],
                         garment_polygon=[[8,15],[57,15],[57,75],[8,75]],protected_rectangles=[[0,0,64,25]],face_rectangle=[20,5,45,24],
                         protection_review='Manually inspected synthetic head region before donor generation')
        self.spec_file=self.root/'spec.json'; self.spec_file.write_text(json.dumps(self.spec))
    def call(self,*args,ok=True):
        result=subprocess.run([os.environ.get('CAIGUANG_TEST_NODE','node'),str(SCRIPT),*map(str,args)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr) if ok else self.assertNotEqual(result.returncode,0,result.stdout)
        return result
    def prepared(self): self.call('prepare',self.spec_file,self.run)
    def test_preserves_head_face_exterior_and_true_feather_with_independent_pixel_check(self):
        self.prepared(); self.call('apply',self.run,self.donor,'1'); self.call('verify',self.run,'1')
        def pixels(file):
            image=Image.open(file)
            return [image.getpixel((x,y)) for y in range(image.height) for x in range(image.width)]
        base=pixels(self.base); donor=pixels(self.donor); out=pixels(self.run/'candidate-v1.png')
        alpha=(self.run/'alpha-v1.bin').read_bytes(); guard=(self.run/'head-guard.bin').read_bytes()
        self.assertTrue(any(0<a<255 for a in alpha),'feather must not accidentally become a binary mask')
        changed=0
        for b,d,o,a,g in zip(base,donor,out,alpha,guard):
            self.assertEqual(o,tuple((bc*(255-a)+dc*a+127)//255 for bc,dc in zip(b,d)))
            if g or not a:self.assertEqual(o,b)
            changed+=o!=b
        self.assertGreater(changed,0)
        self.assertEqual(json.loads((self.run/'result-v1.json').read_text())['visual_qa'],'pending')
    def test_changed_mother_and_incomplete_guard_block_before_output(self):
        for key,value in [('base_sha256','0'*64),('protected_rectangles',[[0,0,64,15]])]:
            spec=dict(self.spec,**{key:value});self.spec_file.write_text(json.dumps(spec))
            self.call('prepare',self.spec_file,self.run,ok=False);self.assertFalse(self.run.exists())
    def test_canvas_mismatch_never_resizes_and_existing_versions_never_overwrite(self):
        self.prepared();Image.new('RGB',(63,96),'red').save(self.donor)
        self.call('apply',self.run,self.donor,'1',ok=False);self.assertFalse((self.run/'candidate-v1.png').exists())
        Image.new('RGB',(64,96),'red').save(self.donor);self.call('apply',self.run,self.donor,'1')
        before=(self.run/'candidate-v1.png').read_bytes();self.call('apply',self.run,self.donor,'1',ok=False)
        self.assertEqual((self.run/'candidate-v1.png').read_bytes(),before)
    def test_local_refinement_versions_keep_frozen_protection_and_old_result(self):
        self.prepared();self.call('apply',self.run,self.donor,'1')
        frozen=(self.run/'head-guard.bin').read_bytes();old=(self.run/'candidate-v1.png').read_bytes()
        refinement=self.root/'refine.json';refinement.write_text(json.dumps(dict(garment_polygon=[[3,10],[61,10],[61,82],[3,82]],reason='Complete synthetic sleeve boundary')))
        self.call('apply',self.run,self.donor,'2',refinement);self.call('verify',self.run,'2')
        self.assertEqual((self.run/'head-guard.bin').read_bytes(),frozen);self.assertEqual((self.run/'candidate-v1.png').read_bytes(),old)
        refinement.write_text(json.dumps(dict(garment_polygon=self.spec['garment_polygon'],reason='test',protected_rectangles=[])))
        self.call('apply',self.run,self.donor,'3',refinement,ok=False)
    def test_tampered_guard_result_or_garment_blocks_verification(self):
        self.prepared();self.call('apply',self.run,self.donor,'1')
        garment = Path(json.loads((self.run/'contract.json').read_text())['garments'][0]['path'])
        for file in [self.run/'head-guard.bin',self.run/'candidate-v1.png',garment]:
            original=file.read_bytes();file.write_bytes(b'tampered');self.call('verify',self.run,'1',ok=False);file.write_bytes(original)
    def test_actual_attachments_use_frozen_bytes_when_external_sources_change(self):
        self.prepared();contract=json.loads((self.run/'contract.json').read_text())
        original_base=self.base.read_bytes();original_garment=self.garment.read_bytes()
        self.base.write_bytes(b'changed outside run');self.garment.write_bytes(b'changed outside run')
        mother,garment=map(Path,contract['tool_parameters']['referenced_image_paths'])
        self.assertTrue(mother.is_relative_to(self.run));self.assertTrue(garment.is_relative_to(self.run))
        self.assertEqual(mother.read_bytes(),original_base);self.assertEqual(garment.read_bytes(),original_garment)
        self.call('apply',self.run,self.donor,'1');self.call('verify',self.run,'1')
    def test_help_has_no_dependency_or_runtime_write_requirement(self):
        env=dict(os.environ);env.pop('NODE_PATH',None)
        out=subprocess.run(['node',str(SCRIPT),'--help'],env=env,capture_output=True,text=True)
        self.assertEqual(out.returncode,0,out.stderr)
    def test_transparency_and_exif_rotation_block_instead_of_silent_normalization(self):
        self.prepared();Image.new('RGBA',(64,96),(230,160,185,128)).save(self.donor)
        self.call('apply',self.run,self.donor,'1',ok=False)
        self.assertFalse((self.run/'candidate-v1.png').exists())
        rotated=self.root/'rotated.jpg';exif=Image.Exif();exif[274]=6
        Image.new('RGB',(64,96),'red').save(rotated,exif=exif)
        self.call('apply',self.run,rotated,'1',ok=False)
        self.assertFalse((self.run/'candidate-v1.png').exists())

if __name__=='__main__':unittest.main()
