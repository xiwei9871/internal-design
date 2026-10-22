import bpy, json
sc=bpy.context.scene
sc.frame_set(112)
dg=bpy.context.evaluated_depsgraph_get()
out=[]
for o in sc.objects:
    if o.type!='LIGHT': continue
    ev=o.evaluated_get(dg)
    m=ev.matrix_world
    cols=[c.name for c in o.users_collection]
    d=o.data
    out.append({'name':o.name,'cols':cols,'type':d.type,
        'x':round(m.translation.x*1000),'y':round(m.translation.y*1000),'z':round(m.translation.z*1000),
        'energy':round(d.energy,1),'color':[round(c,3) for c in d.color]})
json.dump(out,open('/Users/xiwei/interior_design/projects/vray_eval_v1/v15_house/cad/lights.json','w'),ensure_ascii=False,indent=1)
print('LIGHTS',len(out))
for o in out: print(o['name'],o['type'],o['x'],o['y'],o['z'],o['energy'],o['cols'])
