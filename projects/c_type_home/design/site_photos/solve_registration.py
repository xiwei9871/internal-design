"""Fit cameras only against stated references and reject unsupported metric claims."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from registration_inputs import VIEWS, CONFIRMED_SCALE, project

OUT=Path(__file__).resolve().parent
results=[]
for n,v in VIEWS.items():
    name=f'SITE_PHOTO_KITCHEN_{n:03d}';wh=v['preview']
    anchors=v['anchors'];parameters=np.array(v['seed'],float)
    fit_success=False;errors=None;projections=[];boundary_hit=False
    if len(anchors)>=4:
        xyz=np.array([a[1] for a in anchors]);target=np.array([a[2] for a in anchors])
        def residual(p):
            uv,z,_=project(p,xyz,wh)
            return np.r_[(uv-target).ravel(),np.minimum(z-.12,0)*1500]
        fit=least_squares(residual,parameters,bounds=v['limits'],x_scale='jac',max_nfev=1800)
        parameters=fit.x;fit_success=bool(fit.success)
        uv,z,rotation=project(parameters,xyz,wh)
        errors=np.linalg.norm(uv-target,axis=1)
        projections=uv.tolist()
        lo=np.array(v['limits'][0]);hi=np.array(v['limits'][1]);span=hi-lo
        boundary_hit=bool(np.any(np.minimum(parameters-lo,hi-parameters)/span < .001))
    else:
        rotation=project(parameters,[[7,2,1]],wh)[2]
    if not anchors or len(anchors)<4:
        confidence='FAILED';classification='DIRECTION_PREVIEW_ONLY_INSUFFICIENT_ANCHORS'
    elif n==1:
        confidence='LOW';classification='LOCAL_RIGID_SCALE_FIT; GLOBAL_ARCHITECTURAL_REGISTRATION_FAILED'
    elif boundary_hit or errors.mean()>25:
        confidence='FAILED';classification='FIT_REJECTED_BOUND_OR_RESIDUAL_OR_CORRESPONDENCE'
    else:
        confidence='LOW';classification='UNCONFIRMED_CORRESPONDENCES'
    holdouts=[]
    if v['checks']:
        hu,_,_=project(parameters,[a[1] for a in v['checks']],wh)
        for (name_,xyz,uv),pred in zip(v['checks'],hu):
            holdouts.append(dict(name=name_,world_m=xyz,observed_preview_px=uv,
                                 projected_preview_px=pred.tolist(),error_preview_px=float(np.linalg.norm(pred-uv)),
                                 correspondence_status='TENTATIVE_ARCHITECTURAL_MATCH_NEEDS_REVIEW'))
    factor=3000/1050 if n in [1,2,5,6] else 4000/1400
    records=[dict(name=a[0],world_m=a[1],observed_preview_px=a[2],
                  projected_preview_px=projections[j] if projections else None,
                  error_fullres_px=float(errors[j]*factor) if errors is not None else None,
                  model_correspondence_verified=v['correspondence_verified']) for j,a in enumerate(anchors)]
    results.append(dict(photo_id=name,camera_name=f'SITE_CAM_KITCHEN_{n:03d}',
        resolution_original=[round(wh[0]*factor),round(wh[1]*factor)],preview_size=wh,
        camera_parameters=dict(position_m=parameters[:3].tolist(),yaw_rad=float(parameters[3]),
            pitch_rad=float(parameters[4]),roll_rad=float(parameters[5]),
            focal_preview_px=float(parameters[6]),focal_fullres_px=float(parameters[6]*factor),
            camera_cv_rotation_rows=rotation.tolist(),principal_point='IMAGE_CENTER_ASSUMPTION',lens_distortion='ZERO_ASSUMPTION_NO_EXIF'),
        anchor_count=len(anchors),verified_reference_anchor_count=len(anchors) if v['correspondence_verified'] else 0,
        verified_B0_XY_anchor_count=0,model_reference_object=v['object'],basis=v['basis'],
        anchor_geometry_rank=v['geometry_rank'],fit_success=fit_success,
        mean_reprojection_error_px=float(errors.mean()*factor) if errors is not None else None,
        max_reprojection_error_px=float(errors.max()*factor) if errors is not None else None,
        confidence=confidence,classification=classification,parameter_bound_hit=boundary_hit,
        usable_for_dimension_estimation=False,
        local_reference_confidence='MEDIUM' if n==1 else 'NOT_ACCEPTED',
        anchors=records,architectural_holdouts=holdouts,warnings=v['warnings']))
report=dict(register='PHOTO_REGISTRATION_REPORT',stage='REGISTRATION_HUMAN_REVIEW',
    confirmed_current_reference_dimensions=CONFIRMED_SCALE,
    method='Bounded pinhole least-squares pose/focal fitting; no B0 or B1 geometry moved',
    interpretation='Numeric convergence is not registration acceptance. Fridge fit fails architectural holdout; other fits lack verified correspondences.',
    photos=results,metric_gate='NOT_PASSED',
    missing_evidence=['six independently verified architectural correspondences per useful view',
                      'current cabinet placement tied to B0 wall/door coordinates',
                      'unoccluded window/corner matches and current finish Z where needed'])
(OUT/'PHOTO_REGISTRATION_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
inventory=json.loads((OUT/'SITE_PHOTO_REGISTER_V01.json').read_text())
for p,r in zip(inventory['photos'],results):
    p['status']='REGISTRATION_'+r['confidence'];p['camera_name']=r['camera_name']
    p['registration_report']='PHOTO_REGISTRATION_REPORT.json'
inventory['human_confirmed_current_dimensions']=CONFIRMED_SCALE
(OUT/'SITE_PHOTO_REGISTER_V01.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2))
print(json.dumps([dict(id=r['photo_id'],confidence=r['confidence'],mean_px=r['mean_reprojection_error_px'],
                      max_px=r['max_reprojection_error_px'],anchors=r['anchor_count']) for r in results],indent=2))
