from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse,unquote
import json,hashlib,re,zipfile
ROOT=Path(__file__).parent
pages=['index','build','extensions','reliability','codex','pi','deepseek','reading']
errors=[]
sections=0
for slug in pages:
 path=ROOT/(slug+'.html');soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
 ids=[x['id'] for x in soup.select('[id]')]
 if len(ids)!=len(set(ids)):errors.append(f'{slug}: duplicate IDs')
 sections+=len(soup.select('article h2'))
 for tag in soup.select('[href], [src]'):
  value=tag.get('href',tag.get('src','')); url=urlparse(value)
  if url.scheme or url.netloc:continue
  target=ROOT/unquote(url.path) if url.path else path
  if not target.exists():errors.append(f'{slug}: missing {value}')
  if url.fragment and target.suffix=='.html':
   other=BeautifulSoup(target.read_text(encoding='utf-8'),'html.parser')
   if not other.find(id=unquote(url.fragment)):errors.append(f'{slug}: bad anchor {value}')
 if soup.select('script[src^="http"], link[href^="http"]'):errors.append(f'{slug}: remote dependency')
 if len(soup.select('.local-toc a'))!=len(soup.select('article h2')):errors.append(f'{slug}: toc mismatch')
print('Pages:',len(pages),'Sections:',sections,'Errors:',errors)
if errors:raise SystemExit(1)

files={
 'openai/codex': ['README.md','sdk/typescript/README.md','sdk/typescript/src/threadOptions.ts','codex-rs/core/README.md','codex-rs/core/src/tools/router.rs','codex-rs/core/src/tools/registry.rs','codex-rs/ext/skills/src/lib.rs'],
 'earendil-works/pi': ['README.md','packages/ai/README.md','packages/agent/README.md','packages/coding-agent/docs/sdk.md','packages/coding-agent/docs/skills.md','packages/coding-agent/docs/extensions.md','packages/coding-agent/docs/packages.md','packages/coding-agent/docs/configuration.md','packages/coding-agent/examples/extensions/hello.ts'],
 'deepseek-ai/deepseek-harness':['README.zh.md','SAFETY.zh.md','docs/architecture.zh.md','docs/cordis-primer.zh.md','docs/agent-lifecycle.zh.md','docs/tool-execution-pipeline.zh.md','docs/cookbook/adding-a-tool.zh.md','docs/cookbook/adding-an-llm-adapter.zh.md','docs/user/develop/basic/index.zh.md','packages/skill/tool-skill/README.zh.md','packages/sdk/client/README.zh.md'],
 'bojieli/ai-agent-book': ['README.md']+['book/chapter'+str(i)+'.md' for i in range(1,11)]}
records=[]
for repo,paths in files.items():
 branch='master' if repo.endswith('harness') else 'main'
 for rel in paths:
  target=ROOT/'research'/repo.split('/')[-1]/rel
  if target.exists():records.append({'repository':repo,'branch':branch,'file':rel,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'source':'https://github.com/'+repo+'/blob/'+branch+'/'+rel})
if records:
 (ROOT/'research/source-manifest.json').write_text(json.dumps({'retrieved':'2026-09-27','note':'Branch snapshots; hashes identify local content, not a verified Git commit. Not a full repository audit.','files':records},ensure_ascii=False,indent=2),encoding='utf-8')
else:
 records=json.loads((ROOT/'research/source-manifest.json').read_text(encoding='utf-8'))['files']

included=[ROOT/(x+'.html') for x in pages]+[ROOT/'README.md',ROOT/'build_site.py',ROOT/'verify_site.py',ROOT/'research/source-manifest.json']
for folder in ['assets','content','examples']:
 included.extend(x for x in (ROOT/folder).rglob('*') if x.is_file() and '__pycache__' not in x.parts and 'runs' not in x.parts and 'output' not in x.parts)
with zipfile.ZipFile(ROOT/'agent-tutorial-offline.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for file in included:archive.write(file,file.relative_to(ROOT))
print('Packaged',len(included),'files; sources',len(records),'ZIP', (ROOT/'agent-tutorial-offline.zip').stat().st_size,'bytes')
