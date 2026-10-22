import bpy, json
sc=bpy.context.scene
dg=bpy.context.evaluated_depsgraph_get()
ROOMS={'次卫':(9150,4600,11450,6600),'主卫':(13100,4650,16300,6450),
 '客卫':(7900,8000,9700,10900),'生活阳台':(1500,650,5700,2400),
 '厨房':(5900,0,7800,4600),'走廊':(8000,4500,13100,8000)}
out={k:[] for k in ROOMS}
for o in sc.objects:
    if o.type not in ('MESH','EMPTY'): continue
    ev=o.evaluated_get(dg)
    try:
        bb=[ev.matrix_world@__import__('mathutils').Vector(v) for v in o.bound_box]
    except: continue
    xs=[v.x*1000 for v in bb];ys=[v.y*1000 for v in bb];zs=[v.z*1000 for v in bb]
    cx,cy=(min(xs)+max(xs))/2,(min(ys)+max(ys))/2
    for rn,(x0,y0,x1,y1) in ROOMS.items():
        if x0<cx<x1 and y0<cy<y1 and max(xs)-min(xs)>120 and max(zs)-min(zs)>50:
            out[rn].append({'n':o.name,'b':[round(min(xs)),round(min(ys)),round(max(xs)),round(max(ys)),round(min(zs)),round(max(zs))]})
            break
for rn,lst in out.items():
    print('=====',rn,len(lst))
    for it in sorted(lst,key=lambda i:-(i['b'][2]-i['b'][0]))[:25]:
        print(it['n'][:42],it['b'])
json.dump(out,open('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad/fixtures.json','w'))
