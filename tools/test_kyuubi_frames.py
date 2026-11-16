"""Validate the newly drawn one-tail form atlas contract without modifying pixels."""
import hashlib
import json
from pathlib import Path
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

class KyuubiFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'art-review/kyuubi-frames.json').read_text())
        cls.image = Image.open(ROOT / 'art-review' / cls.data['source'])

    def test_authored_sheet_provenance_and_fixed_body_scale(self):
        self.assertEqual(self.image.size, (1024, 1536))
        self.assertEqual(self.data['facing'], 'right')
        self.assertEqual(self.data['source'], 'redrawn/one-tail-v2.png')
        self.assertEqual(self.image.mode, 'RGBA')
        alpha_min, alpha_max = self.image.getchannel('A').getextrema()
        self.assertEqual(alpha_min, 0)
        self.assertGreaterEqual(alpha_max, 250)
        self.assertNotIn('background', self.data)
        mapping = json.loads((ROOT/'art-review/redrawn/atlas-map.json').read_text())['one-tail']
        self.assertEqual(self.data['bodyHeight'], mapping['bodyHeight'])
        self.assertGreater(self.data['bodyHeight'], 0)
        provenance = json.loads((ROOT/'art-review/redrawn/provenance.json').read_text())
        record = next(item for item in provenance['outputs'] if item['file'] == self.data['source'])
        self.assertEqual(record['kind'], 'newly drawn bitmap')
        self.assertEqual(hashlib.sha256((ROOT/'art-review'/self.data['source']).read_bytes()).hexdigest(), record['sha256'])

    def test_every_source_rectangle_and_foot_anchor_is_valid(self):
        width, height = self.image.size
        for name, animation in self.data['animations'].items():
            self.assertGreater(animation['fps'], 0, name)
            self.assertTrue(animation['frames'], name)
            for frame in animation['frames']:
                x, y, w, h = frame['rect']
                self.assertTrue(0 <= x < x + w <= width, name)
                self.assertTrue(0 <= y < y + h <= height, name)
                ax, ay = frame['anchor']
                self.assertTrue(0 <= ax <= w, (name, frame))
                self.assertTrue(0 <= ay <= h + 16, (name, frame))
                self.assertTrue(self.image.crop((x,y,x+w,y+h)).getchannel('A').getbbox(), name)
                self.assertEqual(frame['bodyHeight'], self.data['bodyHeight'])
                self.assertTrue(0 <= frame['atlasIndex'] < 24)

    def test_complete_form_lifecycle_uses_real_pose_sequences(self):
        expected = {'idle': list(range(4)), 'walk': list(range(4,8)),
                    'run': list(range(4,8)), 'hurt': list(range(8,12)),
                    'attack': list(range(12,16)), 'throw': list(range(20,24)),
                    'activation': list(range(4)), 'rasenganCharge': [16,17],
                    'rasenganDash': [18], 'rasenganRelease': [18],
                    'rasenganRecover': [19]}
        self.assertEqual(set(self.data['animations']), set(expected))
        for name, indices in expected.items():
            animation = self.data['animations'][name]
            self.assertEqual([f['atlasIndex'] for f in animation['frames']], indices, name)
            self.assertEqual(animation['loop'], name in ('idle','walk','run','rasenganDash'), name)
        self.assertEqual(self.data['animations']['walk']['frames'], self.data['animations']['run']['frames'])

    def test_vertical_directions_cover_the_complete_action_family(self):
        vertical = self.data['directional']
        image = Image.open(ROOT / 'art-review' / vertical['source'])
        self.assertEqual(image.mode, 'RGBA')
        self.assertEqual(image.getchannel('A').getextrema(), (0, 255))
        self.assertEqual(set(vertical['animations']), {'up', 'down'})
        self.assertNotEqual(vertical['source'], self.data['source'])
        provenance = json.loads((ROOT / 'art-review/redrawn/one-tail-vertical-v1.provenance.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT/'art-review'/vertical['source']).read_bytes()).hexdigest(), provenance['sha256'])
        for direction, animations in vertical['animations'].items():
            self.assertEqual(set(animations), set(self.data['animations']))
            for name, animation in animations.items():
                for frame in animation['frames']:
                    x, y, w, h = frame['rect']
                    self.assertTrue(0 <= x < x+w <= image.width, (direction, name))
                    self.assertTrue(0 <= y < y+h <= image.height, (direction, name))
                    self.assertTrue(image.crop((x,y,x+w,y+h)).getchannel('A').getbbox())
                    self.assertEqual(frame['bodyHeight'], vertical['bodyHeight'])
                    self.assertTrue(0 <= frame['anchor'][0] <= w)
                    self.assertTrue(0 <= frame['anchor'][1] <= h)
                    self.assertEqual(frame['atlasIndex']//4%2, 0 if direction=='down' else 1)
                    if frame.get('orb'):
                        ox, oy, radius = frame['orb']
                        self.assertTrue(0 <= ox <= w and 0 <= oy <= h)
                        self.assertGreater(radius, 0)

    def test_directional_registration_is_reproducible_and_head_scaled(self):
        from copy import deepcopy
        from statistics import median
        from register_kyuubi_directions import register
        from build_redrawn_atlases import hair_width
        self.assertEqual(register(deepcopy(self.data))['directional'], self.data['directional'])
        side = self.data
        vertical = side['directional']
        image = Image.open(ROOT / 'art-review' / vertical['source'])
        head = median(hair_width(self.image, frame)*55/side['bodyHeight']
                      for frame in side['animations']['idle']['frames'])
        for direction in ('up', 'down'):
            other = median(hair_width(image, frame)*55/vertical['bodyHeight']
                           for frame in vertical['animations'][direction]['idle']['frames'])
            self.assertLess(abs(head-other), 1)

if __name__ == '__main__':
    unittest.main()
