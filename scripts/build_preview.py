"""Build a self-contained interactive demo; no credentials, server or external assets."""
import argparse
import json
from pathlib import Path
from ui_server import Service

ROOT=Path(__file__).resolve().parents[1]

def build(output):
    fixtures={name:Service().demo(name) for name in ("coupon","extra","none")}
    html=(ROOT/"web/index.html").read_text(encoding="utf-8")
    html=html.replace('<link rel="stylesheet" href="/style.css">', '<style>'+(ROOT/"web/style.css").read_text(encoding="utf-8")+'</style>')
    scripts=[]
    for name in ("buddy-rules.js","buddy.js","app.js"):
        html=html.replace('<script src="/'+name+'" defer></script>', '')
        scripts.append((ROOT/"web"/name).read_text(encoding="utf-8"))
    html=html.replace('href="/" aria-label', 'href="#" aria-label')
    seed=json.dumps(fixtures,ensure_ascii=False).replace('<',chr(92)+'u003c')
    pool=json.dumps(Service().demo_suggestions({'budget':'25','coupon':'demo'}),ensure_ascii=False).replace('<',chr(92)+'u003c')
    injected='<script>window.__OFFLINE_DEMOS='+seed+';window.__OFFLINE_SUGGESTIONS='+pool+';</script>'
    injected+=''.join('<script>'+s.replace('</script', '<'+chr(92)+'/script')+'</script>' for s in scripts)
    html=html.replace('</body>',injected+'</body>')
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(html,encoding="utf-8")
    return output

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="生成单文件离线交互演示，不查询MCP")
    parser.add_argument("--output",required=True,type=Path)
    print(build(parser.parse_args().output))
