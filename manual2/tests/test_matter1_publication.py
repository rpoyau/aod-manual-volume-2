"""Real source/artifact mutations and semantic-link checks for paired publication."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from publication_support import verify_foundation, verify_main_binding, verify_publication, inspect_pdf_links, semantic_main_destinations, digest


class PublicationTests(unittest.TestCase):
    def copy_bound_main(self, directory):
        target=Path(directory)
        manifest=json.loads((ROOT/'manual2/evidence/foundation-source.json').read_text())
        paths=list(manifest['files'])+['manual2/evidence/foundation-source.json','main.pdf','main.aux','main.fls','main-build-binding.tex','main-build-binding.json']
        for name in paths:
            destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,destination)
        return target

    def expect_rejected_unchanged(self, root, pattern):
        before={p.relative_to(root).as_posix():digest(p) for p in root.rglob('*') if p.is_file()}
        with self.assertRaisesRegex((ValueError,OSError),pattern):
            verify_main_binding(root)
        after={p.relative_to(root).as_posix():digest(p) for p in root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)

    def mutate_publication_receipt(self, change, pattern):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.copy_bound_main(tmp)
            shutil.copytree(ROOT/'manual2',root/'manual2',dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            shutil.copy2(ROOT/'manual2.pdf',root/'manual2.pdf')
            p=root/'manual2/evidence/publication-build.json'
            value=json.loads(p.read_text());change(value);p.write_text(json.dumps(value))
            before={str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError,pattern):
                verify_publication(root,inspect_fonts=False)
            after={str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file()}
            self.assertEqual(before,after)

    def test_missing_publication_artifact_receipt_entry_rejected(self):
        for name in ('main.pdf','manual2/main.pdf','manual2.pdf'):
            with self.subTest(name=name):
                self.mutate_publication_receipt(lambda v:v['published_artifacts'].pop(name),
                                                'Incomplete publication artifact binding')

    def test_stale_publication_foundation_rejected(self):
        self.mutate_publication_receipt(lambda v:v.update(foundation_source_digest='0'*64),
                                        'Stale publication foundation binding')

    def test_forged_publication_page_count_rejected(self):
        self.mutate_publication_receipt(lambda v:v.update(main_pages=999),
                                        'Publication Main page count mismatch')

    def test_current_publication_and_final_figure(self):
        result=verify_publication(ROOT)
        self.assertTrue(result['manual_text_equal'])
        self.assertTrue(result['main_text_matches_release'])
        self.assertEqual(result['main_pages'],69)
        self.assertGreater(result['root_main_links'],0)
        self.assertEqual(result['root_main_links'],result['nested_main_links'])
        self.assertGreaterEqual(result['chart']['minimum_font_pt'],8.99)

    def test_missing_main_aux_rejected_without_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.copy_bound_main(tmp)
            (root/'main.aux').unlink()
            self.expect_rejected_unchanged(root,'Main artifact mismatch')

    def test_changed_main_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.copy_bound_main(tmp)
            with (root/'appendices/H_combinatorics_rd_tests.tex').open('a') as f:f.write('\n% controlled source mutation\n')
            self.expect_rejected_unchanged(root,'Pinned Main source/input mismatch')

    def test_corrupted_pdf_rejected_without_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.copy_bound_main(tmp)
            with (root/'main.pdf').open('ab') as f:f.write(b'CONTROLLED_CORRUPTION')
            self.expect_rejected_unchanged(root,'Main artifact mismatch')

    def test_stale_main_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.copy_bound_main(tmp)
            p=root/'main-build-binding.json';value=json.loads(p.read_text());value['source_digest']='0'*64;p.write_text(json.dumps(value))
            self.expect_rejected_unchanged(root,'Stale Main source binding')

    def test_missing_main_receipt_artifact_entry_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.copy_bound_main(tmp)
            p=root/'main-build-binding.json';value=json.loads(p.read_text())
            value['artifacts'].pop('main.aux');p.write_text(json.dumps(value))
            self.expect_rejected_unchanged(root,'Incomplete Main build binding')

    def test_wrong_published_pdf_target_rejected(self):
        with self.assertRaisesRegex(ValueError,'Wrong Main PDF target'):
            inspect_pdf_links(ROOT/'manual2/main.pdf','main.pdf',ROOT/'main.pdf')

    def test_actual_broken_semantic_destination_rejected(self):
        from pypdf import PdfReader,PdfWriter
        from pypdf.generic import TextStringObject,NameObject
        reader=PdfReader(ROOT/'manual2.pdf');writer=PdfWriter();writer.clone_document_from_reader(reader)
        changed=False
        for page in writer.pages:
            for ref in page.get('/Annots',[]):
                action=ref.get_object().get('/A')
                if action is not None and action.get_object().get('/S')=='/GoToR':
                    action.get_object()[NameObject('/D')]=TextStringObject('FORGED_MISSING_MAIN_LABEL');changed=True;break
            if changed:break
        self.assertTrue(changed)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'corrupt.pdf';writer.write(path)
            before=digest(path)
            with self.assertRaisesRegex(ValueError,'Unknown Main PDF destination'):
                inspect_pdf_links(path,'main.pdf',ROOT/'main.pdf')
            self.assertEqual(digest(path),before)

    def test_missing_semantic_link_rejected_when_other_links_remain(self):
        from pypdf import PdfReader,PdfWriter
        from pypdf.generic import ArrayObject,NameObject
        required=semantic_main_destinations(ROOT)
        target=next(iter(required))
        reader=PdfReader(ROOT/'manual2.pdf');writer=PdfWriter();writer.clone_document_from_reader(reader)
        removed=0
        for page in writer.pages:
            kept=[]
            for ref in page.get('/Annots',[]):
                action=ref.get_object().get('/A')
                if (action is not None and action.get_object().get('/S')=='/GoToR'
                        and action.get_object().get('/D')==target):
                    removed+=1
                else:
                    kept.append(ref)
            if '/Annots' in page:
                page[NameObject('/Annots')]=ArrayObject(kept)
        self.assertGreater(removed,0)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'missing-link.pdf';writer.write(path);before=digest(path)
            with self.assertRaisesRegex(ValueError,'Missing semantic Main PDF links'):
                inspect_pdf_links(path,'main.pdf',ROOT/'main.pdf',required)
            self.assertEqual(digest(path),before)


if __name__=='__main__':unittest.main()
