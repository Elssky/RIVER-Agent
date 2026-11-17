from pathlib import Path
import re,json,html,hashlib
import markdown
from bs4 import BeautifulSoup

ROOT=Path(__file__).parent
PAGES=[
 ('index','01','从零设计 Agent','FOUNDATIONS','把目标、模型、上下文、工具和反馈，组装成一个可控的系统。'),
 ('build','02','实现你的第一个 Agent','IMPLEMENTATION','从接口契约到真实模型接入，逐步跑通一个有边界的 agent loop。'),
 ('extensions','03','Skill、插件与 MCP','EXTENSIBILITY','把可复用流程和可执行能力分开设计，再通过适配层组合。'),
 ('reliability','04','让 Agent 可靠地工作','RELIABILITY','处理长任务、恢复、权限、评估与多 Agent 协作。'),
 ('codex','05','深入 Codex','SOURCE TOUR / CODEX','学习 Rust 核心、工具执行边界，以及 SDK 与 App Server 集成。'),
 ('pi','06','深入 Pi','SOURCE TOUR / PI','学习模型抽象、可嵌入循环，以及 TypeScript 扩展的设计。'),
 ('deepseek','07','深入 DeepSeek Harness','SOURCE TOUR / DSH','理解 Cordis、服务依赖、可逆注册，以及一切皆插件的组装方式。'),
 ('reading','08','阅读路线与资料索引','READING ROOM','把《深入理解 AI Agent》与三份源码连接起来，形成自己的学习路线。'),
]

def mascot():
 return (ROOT/'assets'/'logo.svg').read_text(encoding='utf-8')

search=[]
for i,(slug,num,title,kicker,desc) in enumerate(PAGES):
 raw=(ROOT/'content'/f'{slug}.md').read_text(encoding='utf-8')
 body=markdown.markdown(raw,extensions=['fenced_code','tables','toc','attr_list','md_in_html'])
 soup=BeautifulSoup(body,'html.parser')
 toc=[]
 for j,h in enumerate(soup.find_all('h2')):
  h['id']=f's{j+1}';toc.append((h['id'],h.get_text()))
  texts=[]
  for el in h.next_siblings:
   if getattr(el,'name',None)=='h2':break
   if getattr(el,'name',None):texts.append(el.get_text(' ',strip=True))
  search.append({'page':slug+'.html','title':title,'id':h['id'],'heading':h.get_text(),'text':' '.join(texts)})
 for table in soup.find_all('table'):
  wrap=soup.new_tag('div',attrs={'class':'table-wrap','tabindex':'0','aria-label':'可横向滚动的表格'});table.wrap(wrap)
 for pre in soup.find_all('pre'):
  pre['tabindex']='0'
 nav=''.join(f'<a class="page-link {"active" if p==slug else ""}" href="{p}.html" {"aria-current=page" if p==slug else ""}><span>{n}</span>{t}</a>' for p,n,t,_,_ in PAGES)
 local=''.join(f'<a href="#{ident}"><span>{j+1:02}</span>{html.escape(t)}</a>' for j,(ident,t) in enumerate(toc))
 prev=PAGES[i-1] if i else None; nxt=PAGES[i+1] if i+1<len(PAGES) else None
 pager=(f'<a href="{prev[0]}.html">← 上一篇<small>{prev[2]}</small></a>' if prev else '<span></span>')+(f'<a href="{nxt[0]}.html">下一篇 →<small>{nxt[2]}</small></a>' if nxt else '<a href="index.html">回到起点<small>带着你的 Agent 再读一次</small></a>')
 count=len(re.findall(r'[\u4e00-\u9fff]',raw))
 page=f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{desc}"><title>{title} · RIVER-Agent Tutorial</title><link rel="icon" type="image/svg+xml" href="assets/logo.svg"><link rel="stylesheet" href="assets/style.css"><script defer src="assets/search-index.js"></script><script defer src="assets/app.js"></script></head>
<body data-page="{slug}"><a class="skip" href="#main">跳到正文</a><div class="top-progress" id="top-progress"></div>
<header class="topbar"><a class="brand" href="index.html"><span class="brand-bot">{mascot()}</span><span>RIVER-Agent Tutorial<small>BUILD · UNDERSTAND · EXPLORE</small></span></a><div class="header-actions"><button id="search-open" aria-label="搜索全部教程">⌕ <span>搜索教程</span><kbd>/</kbd></button><button id="font-toggle" aria-label="切换较大字体">Aa</button><button id="print" aria-label="打印当前篇">打印</button><button id="menu-toggle" aria-expanded="false" aria-controls="sidebar">目录 ☰</button></div></header>
<div class="layout"><aside id="sidebar"><div class="side-label">学习地图 <span>8 篇</span></div><nav aria-label="篇章导航">{nav}</nav><div class="side-label local-label">本篇目录</div><nav class="local-toc" aria-label="本篇章节">{local}</nav><div class="side-note">从一个小循环开始<br>让每一步都有证据。<span>本地阅读 · 无外部资源依赖</span></div></aside>
<main id="main"><div class="chapter-meta"><span>{kicker}</span><span>约 {max(5,round(count/230))} 分钟 · {len(toc)} 节</span></div><div class="chapter-head"><div><h1>{title}</h1><p>{desc}</p></div><div class="head-bot">{mascot()}<span>实验笔记 {num}</span></div></div><div class="source-note">资料核对：2026-09-27 <span>项目事实附来源；自建方案与教学简化会明确标注。</span></div>
<article>{soup}</article><div class="chapter-complete"><label><input type="checkbox" id="completed"> 我已读完这一篇</label><span id="complete-count"></span></div><nav class="pager" aria-label="上一篇与下一篇">{pager}</nav><footer>RIVER-Agent Tutorial · 原创学习教程 · 外部资料版权归原作者所有<br>页面与练习可以离线使用；外部来源链接与真实模型请求需要网络。</footer></main></div>
<dialog id="search-dialog" aria-labelledby="search-title"><div class="search-head"><h2 id="search-title">搜索全部教程</h2><button id="search-close" aria-label="关闭搜索">×</button></div><input id="search-input" type="search" placeholder="试试：skill、工具调用、沙箱、恢复…" aria-label="搜索关键词"><p id="search-status" role="status">输入关键词，搜索全部 8 篇教程。</p><div id="search-results"></div></dialog><div id="toast" role="status"></div></body></html>'''
 (ROOT/f'{slug}.html').write_text(page,encoding='utf-8')
(ROOT/'assets'/'search-index.js').write_text('window.SEARCH_INDEX = '+json.dumps(search,ensure_ascii=False)+';',encoding='utf-8')
print('Generated',len(PAGES),'pages and',len(search),'search sections')
