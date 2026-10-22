"""Explicit observed image features; uncertain correspondences are never counted as verified."""
import numpy as np

CONFIRMED_SCALE={'countertop_height_mm':820,'countertop_depth_mm':600,
                 'fridge_width_mm':905,'fridge_depth_mm':710,'fridge_height_mm':1700,
                 'authority':'HUMAN_CONFIRMED_CURRENT_SAME_AS_INITIAL_PDF'}

# Coordinates measured on the preserved 1400-pixel-long-edge preview grids.
# Each point retains its observed feature and the chosen model correspondence.
VIEWS={
1:dict(preview=[1050,1400],seed=[6.35,2.0,1.45,1.05,-.22,.015,1500],
       limits=[[4.8,.6,1.05,.20,-.70,-.25,800],[7.15,3.65,1.90,2.40,.25,.25,3000]],
       object='B11_K-FRIDGE',basis='HUMAN_CONFIRMED_RIGID_FRIDGE_FRONT + FROZEN_LOWER_FLOOR_Z',
       correspondence_verified=True,geometry_rank=2,anchors=[
       ('fridge_front_top_left',[6.835,3.750,1.700],[430,454]),
       ('fridge_front_top_mid',[7.2875,3.750,1.700],[600,466]),
       ('fridge_front_top_right',[7.740,3.750,1.700],[750,482]),
       ('fridge_front_bottom_left',[6.835,3.750,0.0],[452,1318]),
       ('fridge_front_bottom_mid',[7.2875,3.750,0.0],[600,1243]),
       ('fridge_front_bottom_right',[7.740,3.750,0.0],[742,1165])],
       warnings=['Six points are coplanar; X/Y placement of the remodeled fridge run is not independently surveyed.',
                 'Cabinet fronts may be offset from refrigerator door plane; estimate uncertainty must include this offset.'],
       checks=[('sliding_partition_right_head',[5.65,4.6225,2.40],[92,298]),
               ('sliding_partition_right_foot',[5.65,4.6225,0.0],[150,1280])]),
2:dict(preview=[1050,1400],seed=[6.45,2.45,1.48,1.12,-.10,.035,1800],
       limits=[[4.8,.6,1.05,.1,-.7,-.3,800],[7.15,3.65,1.90,2.5,.3,.3,3400]],
       object='B11_K-FRIDGE',basis='PARTIAL_FRIDGE_FRONT; INSUFFICIENT_KNOWN_CORNERS',
       correspondence_verified=False,geometry_rank=2,anchors=[
       ('fridge_top_mid',[7.2875,3.75,1.70],[129,447]),
       ('fridge_top_right',[7.740,3.75,1.70],[316,477]),
       ('fridge_bottom_right',[7.740,3.75,0.0],[354,1312])],warnings=['Top/left/bottom portions are cropped; only three candidate rigid points.'],checks=[]),
3:dict(preview=[1400,1050],seed=[5.25,2.28,1.48,.03,-.12,.01,1500],
       limits=[[3.8,.4,1.05,-.7,-.6,-.25,850],[6.9,3.6,1.90,.7,.3,.25,3400]],
       object='B11_K-COOK',basis='INITIAL_CABINET_PDF_REFERENCE_HYPOTHESIS; MODULE_LOCATIONS_UNCONFIRMED',
       correspondence_verified=False,geometry_rank=3,anchors=[
       ('cook_counter_front_north',[7.2,3.3,.82],[449,822]),
       ('cook_counter_front_south',[7.2,2.4,.82],[802,790]),
       ('hood_front_north_low',[7.42,3.3,1.6],[447,611]),
       ('hood_front_south_low',[7.42,2.4,1.6],[776,601]),
       ('upper_front_north_low',[7.42,3.3,1.67],[452,426]),
       ('upper_front_south_low',[7.42,2.4,1.67],[812,440]),
       ('upper_south_low',[7.42,.535,1.67],[1260,441]),
       ('upper_south_high',[7.42,.535,2.41],[1256,190])],
       warnings=['Cooktop/hood and cabinet module origins in initial PDF may have changed.',
                 'The hood body is generic in B1; its edges are not surveyed anchors.'],checks=[]),
4:dict(preview=[1400,1050],seed=[6.40,2.8,1.48,-1.68,-.15,.06,1500],
       limits=[[4.8,.8,1.05,-2.2,-.6,-.3,850],[7.2,4.1,1.9,-.8,.3,.3,3400]],
       object='GLZ_W-KIT-S',basis='PARTIALLY_OCCLUDED_WINDOW; CURRENT_COLUMN/RETURN NOT REGISTERED',
       correspondence_verified=False,geometry_rank=2,anchors=[
       ('window_image_left_head',[7.1,-.1,2.4],[518,105]),
       ('window_image_right_head',[6.1,-.1,2.4],[661,70]),
       ('window_image_right_sill',[6.1,-.1,.45],[660,489])],
       warnings=['Boiler/person/cabinet obstruct window frame corners. Initial sill/head assumptions require independent checking.'],checks=[]),
5:dict(preview=[1050,1400],seed=[6.35,1.95,1.48,-1.50,-.14,-.02,1600],
       limits=[[5.1,.5,1.05,-2.1,-.6,-.3,750],[7.15,3.6,1.9,-.8,.35,.3,3400]],
       object='GLZ_W-KIT-S',basis='FROZEN_WINDOW_REFERENCE_HYPOTHESIS; SILL OCCLUDED',
       correspondence_verified=False,geometry_rank=2,anchors=[
       ('window_image_left_head',[7.1,-.1,2.4],[93,10]),
       ('window_image_right_head',[6.1,-.1,2.4],[503,24]),
       ('window_image_left_sill',[7.1,-.1,.45],[111,575]),
       ('window_image_right_sill',[6.1,-.1,.45],[504,574])],
       warnings=['Window head partly cropped; sill-left/right hidden or partly obscured.',
                 'A four-corner candidate fit is not independent validation of frozen window Z against the renovated finish.'],checks=[]),
6:dict(preview=[1050,1400],seed=[4.15,2.90,1.45,-1.38,.0,-.04,1500],
       limits=[[1.6,.75,1.05,-2.2,-.6,-.3,750],[5.4,4.0,1.9,-.6,.3,.3,3400]],
       object='GLZ_W-LBALC-S',basis='ADJACENT_CABINET_IDENTITY_UNRESOLVED; NO_FIT',
       correspondence_verified=False,geometry_rank=0,anchors=[],
       warnings=['Window is cropped and cabinet cannot yet be tied to R029/R032 or a new position. Pose is a direction preview only.'],checks=[])
}

def project(parameters,points,image_size):
    cx,cy,cz,yaw,pitch,roll,f=parameters
    forward=np.array([np.cos(pitch)*np.cos(yaw),np.cos(pitch)*np.sin(yaw),np.sin(pitch)])
    right=np.cross(forward,[0,0,1.0]);right/=np.linalg.norm(right)
    down=np.cross(forward,right)
    r2=np.cos(roll)*right+np.sin(roll)*down
    d2=-np.sin(roll)*right+np.cos(roll)*down
    rot=np.stack([r2,d2,forward])
    local=(np.asarray(points)-np.array([cx,cy,cz]))@rot.T
    depth=local[:,2]
    uv=f*local[:,:2]/np.maximum(depth[:,None],.02)+np.array(image_size)/2
    return uv,depth,rot
