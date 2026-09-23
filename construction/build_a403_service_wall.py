"""Service wall coordination detail: calibrated bay widths, assumed cabinet heights."""
from cad_common import (DATA, MM, OUT, new_doc, add_text, draw_frame_and_title,
                        render_preview)
from build_a401_elevations import elem
from ezdxf.enums import TextEntityAlignment


def build_document():
    doc=new_doc()
    msp=doc.modelspace()
    service=DATA['design']['service_wall']
    total=sum(b['width_mm'] for b in service['bays'])
    height=service['height_mm']
    depth=service['rect_px'][2]*MM
    ceil=DATA['design']['ceiling_mm']['dry']
    def dim(p1,p2,base,angle=0,text='<>'):
        d=msp.add_linear_dim(p1=p1,p2=p2,base=base,angle=angle,text=text,dimstyle='ARCH',
            override={'dimtxt':60,'dimasz':40,'dimexe':40,'dimexo':20,'dimgap':20},
            dxfattribs={'layer':'A-DIMS'})
        d.render()
    def text(s,x,y,h=65):
        add_text(msp,s,h,(x,y))

    text('01  服务墙正立面 / 西向看 · 北在右',0,3000,90)
    msp.add_line((-150,0),(total+150,0),dxfattribs={'layer':'A-WALL','lineweight':50})
    msp.add_line((0,ceil),(total,ceil),dxfattribs={'layer':'A-CEIL','linetype':'DASHED'})
    text('吊顶完成面 +2600（假设）',0,2720)
    x=0
    starts={}
    labels={'fridge':'冰箱区','oven':'蒸烤区','laundry':'洗烘区'}
    # Physical east-corridor view reverses north-to-south source ordering.
    for bay in reversed(service['bays']):
        w=bay['width_mm'];starts[bay['id']]=x
        elem(msp,0,0,x,0,w,height,'',lw=35)
        add_text(msp,labels[bay['id']],65,(x+w/2,height+70),TextEntityAlignment.MIDDLE_CENTER)
        dim((x,0),(x+w,0),(x,-160))
        x+=w
    dim((0,0),(total,0),(0,-380))
    dim((0,0),(0,height),(-240,0),90)
    names={'fridge':'01 冰箱','oven':'02 烤箱','steam':'03 蒸箱','washer':'04 洗衣机','dryer':'05 干衣机'}
    for appliance in service['appliances']:
        bay=next(b for b in service['bays'] if b['id']==appliance['bay'])
        x=starts[bay['id']]+(bay['width_mm']-appliance['width_mm'])/2
        z=appliance['z_mm']; w=appliance['width_mm'];h=appliance['height_mm']
        elem(msp,0,0,x,z,w,h,'',layer='A-FIXT')
        add_text(msp,names[appliance['id']],62,(x+w/2,z+h/2),TextEntityAlignment.MIDDLE_CENTER)
        if appliance['id'] in ('washer','dryer'):
            msp.add_circle((x+w/2,z+h*.43),w*.3,dxfattribs={'layer':'A-FIXT'})
        elif appliance['id'] in ('steam','oven'):
            elem(msp,0,0,x+50,z+70,w-100,h-200,'',layer='A-FIXT')
            msp.add_line((x+50,z+h-90),(x+w-50,z+h-90),dxfattribs={'layer':'A-FIXT'})

    # Rotated local plan presents northern fridge bay at the left.
    py=-1900
    text('02  平面展开 / 北端在左 · 柜前为过道',0,py+700,85)
    x=0
    for bay in service['bays']:
        elem(msp,0,py,x,0,bay['width_mm'],depth,'',lw=35)
        add_text(msp,labels[bay['id']],65,(x+bay['width_mm']/2,py+depth/2),TextEntityAlignment.MIDDLE_CENTER)
        dim((x,py),(x+bay['width_mm'],py),(x,py-150))
        x+=bay['width_mm']
    dim((total,py),(total,py+depth),(total+240,py),90)
    text('开门方向、走管槽及散热净空待SKU确认',0,py-360)

    sx=3550
    text('03  柜体侧剖 / 外包络',sx-100,3000,90)
    elem(msp,sx,0,0,0,depth,height,'',lw=35)
    msp.add_line((sx-100,ceil),(sx+depth+100,ceil),dxfattribs={'layer':'A-CEIL','linetype':'DASHED'})
    dim((sx,0),(sx+depth,0),(sx,-200))
    dim((sx+depth,0),(sx+depth,height),(sx+depth+220,0),90)
    dim((sx+depth,height),(sx+depth,ceil),(sx+depth+480,height),90)
    for i,line in enumerate(['H2400暂定','设备净深/背板','散热与检修空间','待厂家安装图确认']):
        text(line,sx+40,1750-i*170,58)
    text('FFL ±0.000',sx,-430)

    tx=5400
    text('设备参考包络 / 非订货及开孔尺寸',tx,2980,90)
    text('编号    宽 × 高    /  底标高（mm）',tx,2730,70)
    for i,a in enumerate(service['appliances']):
        text(f"{names[a['id']]}    {a['width_mm']} × {a['height_mm']}  /  +{a['z_mm']}",tx,2480-i*190,68)
    rows=[
        '01 总宽2297.88、深618.66来自A7标定；',
        '     图面取整标注，生产前逐格现场复尺。',
        '02 三列顺序已确认：冰箱 / 蒸烤 / 洗烘。',
        '03 柜高2400和设备高程为设计假设。',
        '04 柜板厚、开孔、铰链与门板开启待确认。',
        '05 洗烘叠放连接件、承重、防振待厂家确认。',
        '06 所有设备SKU、散热及检修净空待确认。',
        '07 插座、水点位置参见A302/A303；需结合',
        '     设备安装图协调，禁止设于不可检修处。',
        '08 本图为设计协调版，不得用于直接下单。',
    ]
    text('协调事项 / HOLD POINTS',tx,1280,85)
    for i,row in enumerate(rows): text(row,tx,1050-i*175,65)
    text('尺寸来源：approved_v14.json / service_wall',tx,-950,60)
    draw_frame_and_title(msp,'服务墙专项协调详图','A403',[
        '三视图均为1:20；mm；以FFL为标高零点。设备及柜体高度仍待选型/现场确认。'])
    return doc


def main():
    doc=build_document()
    doc.saveas(OUT/'A403_服务墙专项详图.dxf')
    render_preview(doc,doc.modelspace(),OUT/'A403_服务墙专项详图_preview.png')


if __name__=='__main__':
    main()
