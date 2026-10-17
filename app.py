"""Project entry point: offline demos and live read-only coupon quote comparison."""
import argparse
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
from render_report import render
from run_live import run_live


def main(argv=None):
    parser = argparse.ArgumentParser(description="麦麦明白点：查询用券前后应付金额，生成中文报告")
    modes = parser.add_subparsers(dest="mode", required=True)
    demo = modes.add_parser("demo", help="离线回放，无Token、无网络、无模型积分消耗")
    demo.add_argument("--case", choices=["coupon", "no-match", "extra-spend", "saving"], default="coupon")
    demo.add_argument("--output", type=Path, default=ROOT / "local/report.html")
    live = modes.add_parser("live", help="用自己的Token实时查询，仅单品默认规格、到店自取")
    live.add_argument("--store", required=True, help="从MCP门店查询取得的门店编码")
    live.add_argument("--product", action="append", required=True, help="实际菜单中的单品编码，可重复参数添加不同商品，每件数量1")
    live.add_argument("--coupon-product", help="要使用券的商品编码；不指定则只核验不用券报价")
    live.add_argument("--coupon-title", help="多张适用券时用券名关键词缩小选择")
    live.add_argument("--budget", required=True, help="预算，单位元，例如25")
    live.add_argument("--need", required=True, help="原始需求文字，不写私人地址或凭证")
    live.add_argument("--needs-status", choices=["pending", "confirmed", "rejected"], default="pending", help="餐品/口味要求是否已确认，预算独立检查；默认待确认")
    live.add_argument("--config", type=Path, help="显式指定本机MCP配置；默认读取环境变量MCD_MCP_TOKEN")
    live.add_argument("--output", type=Path, default=ROOT / "local/live-report.html")
    args = parser.parse_args(argv)
    try:
        if args.mode == "demo":
            files = {"coupon": ("coupon-price-only.json", True), "no-match": ("latest-quotes.json", True),
                     "extra-spend": ("demo-quotes.json", False), "saving": ("demo-saving.json", False)}
            name, adapted = files[args.case]
            document = json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))
            html = render(document, adapted=adapted)
            evidence = None
        else:
            document, evidence = run_live(args)
            html = render(document, adapted=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if evidence is not None:
            args.output.with_suffix(".evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
            args.output.with_suffix(".quotes.json").write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
        args.output.write_text(html, encoding="utf-8")
        print("报告已生成：" + str(args.output.resolve()))
        print("双击HTML查看。报告不会自动刷新；未下单、领券、兑换或支付。")
        return 0
    except HTTPError as exc:
        print("连接失败，HTTP状态 " + str(exc.code) + "。401请检查Token，429请稍后再试；未生成本轮报告。", file=sys.stderr)
    except (URLError, TimeoutError):
        print("网络连接失败或超时；未生成本轮报告。", file=sys.stderr)
    except (ValueError, KeyError, TypeError, OSError):
        print("未能生成本轮报告：请检查参数、凭证、餐品规格和券适用性。响应格式可能不受支持；不会输出原始凭证或响应。", file=sys.stderr)
    return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
