"""Source-typography regression tests: headings, emphasis and literal tokens."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from restore_fallout_document_layouts import raw_layout,compact
class SourceLayoutTests(unittest.TestCase):
 def titles(self,source):
  text,norm,heads,breaks=raw_layout(source)
  return [norm[a:b] for a,b,level,basis in heads]
 def test_broken_bold_does_not_promote_list(self):
  raw="<font size='16'><b><p align='center'>협회 소식</p></font><font size='12'><p>- 첫째\n- 둘째</p>"
  self.assertEqual(self.titles(raw),['협회소식'])
 def test_uniform_handwritten_letter_is_not_heading(self):
  self.assertEqual(self.titles("<p align='left'><font face='$HandwrittenFont' size='22'>안녕, 얘야.\n\n사랑을 담아,\n아빠가</font></p>"),[])
 def test_newspaper_title_byline_and_body(self):
  raw='<p align="center">미래가 두렵습니까?\n글\n파이퍼 라이트</p>[pagebreak]<p align="left">우리는 모두 굴복하고 있었다. 이 이야기는 길게 이어집니다.</p>'
  self.assertEqual(self.titles(raw),['미래가두렵습니까?','파이퍼라이트'])
 def test_inline_emphasis_stays_in_prose(self):
  self.assertEqual(self.titles('<p>이 문장은 <b>강조한 단어</b>를 포함하는 일반 문장입니다.</p>'),[])
 def test_alias_token_remains_literal(self):
  text,norm,heads,breaks=raw_layout('<p>이름: <Alias=Player>\n<Token.Name=Value></p>')
  self.assertIn('<Alias=Player>',text);self.assertIn('<Token.Name=Value>',text)
 def test_default_body_size_does_not_become_heading(self):
  raw="<font size='18'>노래의 본문입니다.\n계속되는 노래의 본문입니다.\n<b>2절</b>\n본문이 계속 이어집니다.</font><font size='17'>[주석]</font>"
  self.assertEqual(self.titles(raw),['2절'])
if __name__=='__main__':unittest.main()
