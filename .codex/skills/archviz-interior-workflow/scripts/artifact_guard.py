#!/usr/bin/env python3
"""Local byte preflight, immutable-file hashes and bounded JPEG review sheets."""
import argparse
import hashlib
import json
import math
from pathlib import Path

DEFAULT_LIMIT=24*1024*1024

def preflight(images,prompt,limit=DEFAULT_LIMIT):
    if not images or limit<=0:raise ValueError("Images and positive byte limit required")
    paths=[Path(p).resolve(strict=True) for p in images]
    rows=[{"path":str(p),"bytes":p.stat().st_size} for p in paths]
    total=sum(r["bytes"] for r in rows)
    estimate=sum(((r["bytes"]+2)//3)*4 for r in rows)+len(prompt.encode("utf-8"))+65536
    if estimate>limit:raise ValueError(f"Input estimate {estimate} bytes exceeds budget {limit} bytes")
    return {"status":"WITHIN_LOCAL_BUDGET","files":rows,"image_bytes":total,
            "estimated_encoded_bytes":estimate,"limit_bytes":limit,
            "note":"Conservative estimate, not actual HTTP bytes or provider acceptance"}

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def snapshot(files):
    paths=[Path(p).resolve(strict=True) for p in files]
    if not paths:raise ValueError("Explicit file list required")
    return {"schema":"archviz.preservation.v1","files":[
        {"path":str(p),"bytes":p.stat().st_size,"sha256":digest(p)} for p in paths]}

def verify(manifest):
    if manifest.get("schema")!="archviz.preservation.v1" or not manifest.get("files"):
        raise ValueError("Invalid preservation manifest")
    rows=[]
    for row in manifest["files"]:
        p=Path(row["path"])
        status="MISSING" if not p.is_file() else "UNCHANGED" if digest(p)==row["sha256"] else "CHANGED"
        rows.append({"path":str(p),"status":status})
    return {"unchanged":all(r["status"]=="UNCHANGED" for r in rows),"files":rows}

def sheet(images,out,max_edge=1600,quality=82,columns=2):
    from PIL import Image,ImageDraw
    paths=[Path(p).resolve(strict=True) for p in images];out=Path(out).resolve()
    if not paths or len(paths)>12:raise ValueError("Use 1–12 explicit images per local sheet")
    if max_edge<256 or max_edge>2000 or not 50<=quality<=95 or columns<1 or columns>6:
        raise ValueError("Review limits: edge 256–2000, quality 50–95, columns 1–6")
    if out.exists():raise FileExistsError(f"Preserve existing file: {out}")
    if out.suffix.lower() not in [".jpg",".jpeg"]:raise ValueError("Review output must be JPEG")
    columns=min(columns,len(paths));rows=math.ceil(len(paths)/columns)
    canvas=Image.new("RGB",(columns*600,rows*365),"#f5f2e9");draw=ImageDraw.Draw(canvas)
    sources=[]
    for i,p in enumerate(paths):
        with Image.open(p) as source:
            sources.append({"path":str(p),"native_size":list(source.size)})
            im=source.convert("RGB");im.thumbnail((590,330))
        x=(i%columns)*600;y=(i//columns)*365
        label=f"{i+1}: {p.parent.name}/{p.name}".encode("ascii","replace").decode()
        draw.text((x+5,y+4),label[:90],fill="#333333");canvas.paste(im,(x+5,y+25))
    canvas.thumbnail((max_edge,max_edge))
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("xb") as handle:canvas.save(handle,format="JPEG",quality=quality)
    return {"path":str(out),"size":list(canvas.size),"bytes":out.stat().st_size,"sources":sources}

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("preflight");p.add_argument("--image",action="append",required=True);p.add_argument("--prompt-file");p.add_argument("--limit-mib",type=float,default=24)
    p=sub.add_parser("sheet");p.add_argument("--image",action="append",required=True);p.add_argument("--out",required=True);p.add_argument("--max-edge",type=int,default=1600);p.add_argument("--quality",type=int,default=82);p.add_argument("--columns",type=int,default=2)
    p=sub.add_parser("snapshot");p.add_argument("--file",action="append",required=True);p.add_argument("--out",required=True)
    p=sub.add_parser("verify");p.add_argument("--manifest",required=True)
    args=parser.parse_args()
    try:
        if args.command=="preflight":
            prompt=Path(args.prompt_file).read_text() if args.prompt_file else ""
            result=preflight(args.image,prompt,int(args.limit_mib*1024*1024))
        elif args.command=="sheet":result=sheet(args.image,args.out,args.max_edge,args.quality,args.columns)
        elif args.command=="snapshot":
            result=snapshot(args.file);out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
            with out.open("x") as handle:json.dump(result,handle,ensure_ascii=False,indent=2)
            result={"path":str(out.resolve()),"file_count":len(result["files"])}
        else:result=verify(json.loads(Path(args.manifest).read_text()))
        print(json.dumps(result,ensure_ascii=False))
        return 0 if result.get("unchanged",True) else 1
    except (OSError,ValueError,ImportError) as exc:
        print(json.dumps({"status":"FAILED","error":str(exc)},ensure_ascii=False));return 2

if __name__=="__main__":raise SystemExit(main())
