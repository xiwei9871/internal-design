"""CD_V01 MEP schematic points (A302 power/control/data, A303 water). All PROPOSED / TBD.
Coordinates follow real model objects (inputs/model_inventory.json) and A202 zones.
H = height above the room's finished floor (mm). Drainage is OUT_OF_SCOPE (owner)."""

# ---- sources: positions unknown -> TBD (drawn as placeholders, never as decided) ----
SOURCES = [
    dict(id='PANEL', kind='POWER_SOURCE', name='强电配电箱', x=2950, y=6800, H=1600, status='TBD',
         note='位置未知, 暂按入户门旁示意; SITE_VERIFY_REQUIRED'),
    dict(id='WEAK', kind='DATA_SOURCE', name='弱电箱/光猫', x=2950, y=7150, H=400, status='TBD',
         note='位置未知, 暂按入户门旁示意; SITE_VERIFY_REQUIRED'),
    dict(id='WATER_IN', kind='COLD_SOURCE', name='给水入户/总阀', x=3000, y=760, H=300, status='TBD',
         note='入户管位置与水表位置未知; SITE_VERIFY_REQUIRED'),
    dict(id='HEATER', kind='HOT_SOURCE', name='热水器', x=4000, y=760, H=1500, status='ASSUMED_TBD',
         note='假定在生活阳台; 型式(燃气/电)与位置待业主确定'),
]

# ---- A303 water points: (id, room, fixture, kind, x, y, H, model source) ----
WATER = [
    ('W01', 'kitchen', '厨房水槽', 'HOT', 6450, 30, 500, 'B11_K-SINK_BOTTOM'),
    ('W02', 'kitchen', '厨房水槽', 'COLD', 6750, 30, 500, 'B11_K-SINK_BOTTOM'),
    ('W03', 'kitchen', '净水器', 'COLD', 6900, 30, 350, 'B11_K-SINK_BOTTOM'),
    ('W04', 'secondary_bath', '台盆', 'HOT', 9700, 6270, 500, 'R3_VANITY_BASIN_REVIEW'),
    ('W05', 'secondary_bath', '台盆', 'COLD', 9950, 6270, 500, 'R3_VANITY_BASIN_REVIEW'),
    ('W06', 'secondary_bath', '马桶', 'COLD', 11250, 4860, 250, 'R3_WC_LATEST'),
    ('W07', 'secondary_bath', '淋浴', 'HOT', 11270, 5950, 1100, 'R3_SHOWER_TRAY'),
    ('W08', 'secondary_bath', '淋浴', 'COLD', 11270, 6150, 1100, 'R3_SHOWER_TRAY'),
    ('W09', 'master_bath', '台盆', 'HOT', 13620, 6370, 500, 'CBM_MASTER_BASIN'),
    ('W10', 'master_bath', '台盆', 'COLD', 13860, 6370, 500, 'CBM_MASTER_BASIN'),
    ('W11', 'master_bath', '马桶', 'COLD', 14850, 6370, 250, 'B11_Rectangle034_CATALOG_00_00'),
    ('W12', 'master_bath', '淋浴', 'HOT', 16170, 5450, 1100, 'B11_Rectangle033 (shower glass)'),
    ('W13', 'master_bath', '淋浴', 'COLD', 16170, 5650, 1100, 'B11_Rectangle033 (shower glass)'),
    ('W14', 'guest_bath', '台盆', 'HOT', 8030, 8500, 500, 'CBM_GUEST_BASIN'),
    ('W15', 'guest_bath', '台盆', 'COLD', 8030, 8750, 500, 'CBM_GUEST_BASIN'),
    ('W16', 'guest_bath', '马桶', 'COLD', 8030, 9580, 250, 'B11_Rectangle008_CATALOG_00_00'),
    ('W17', 'guest_bath', '淋浴', 'HOT', 8750, 10670, 1100, 'B11_Rectangle007 (shower glass)'),
    ('W18', 'guest_bath', '淋浴', 'COLD', 8950, 10670, 1100, 'B11_Rectangle007 (shower glass)'),
    ('W19', 'study', '茶水台盆', 'HOT', 14350, 6630, 500, 'R3_TEA_SINK_BOTTOM'),
    ('W20', 'study', '茶水台盆', 'COLD', 14550, 6630, 500, 'R3_TEA_SINK_BOTTOM'),
    ('W21', 'north_sunroom', '洗衣机', 'COLD', 8400, 11140, 1100, 'SUNROOM_LAUNDRY_*'),
    ('W22', 'service_balcony', '备用(拖把池等)', 'COLD', 5500, 1500, 600, 'owner TBD'),
]
WATER_STATUS = {'W03': 'PROPOSED', 'W22': 'OPTIONAL_TBD'}

# ---- A302 power / data / alarm points: (id, room, type, x, y, H, model source, note) ----
POWER = [
    # living / dining / entry
    ('S01', 'living', 'SOCKET', 2930, 7950, 300, 'HOUSE_V1_SOFA_CHAISE_COMPLETE', '沙发南端'),
    ('S02', 'living', 'SOCKET', 2930, 11300, 300, 'HOUSE_V1_SOFA_2_V10', '沙发北端'),
    ('S03', 'living', 'SOCKET', 7730, 9500, 300, 'V4_Console_solid_ash_top', '电视墙'),
    ('S04', 'living', 'SOCKET', 7730, 10700, 300, 'V4_Console_solid_ash_top', '电视墙'),
    ('S05', 'living', 'SOCKET_16A_AC', 7730, 11000, 2200, '-', '客厅空调'),
    ('S06', 'living', 'SOCKET', 2930, 3300, 300, 'V4_Dining_racetrack_38mm_top', '餐桌旁'),
    ('S07', 'living', 'SOCKET_16A_AC', 2930, 4600, 2200, '-', '餐厅空调'),
    # kitchen
    ('S10', 'kitchen', 'SOCKET', 7780, 1000, 1100, 'B11_K-RUN-E_COUNTER', '台面(吊柜下)'),
    ('S11', 'kitchen', 'SOCKET', 7780, 1900, 1100, 'B11_K-RUN-E_COUNTER', '台面(吊柜下)'),
    ('S12', 'kitchen', 'SOCKET', 7780, 3550, 1100, 'B11_K-RUN-E_COUNTER', '台面(吊柜下)'),
    ('S13', 'kitchen', 'APPLIANCE', 7780, 2850, 2100, 'B11_K-COOK_HOOD_REVIEW', '油烟机(吊柜内)'),
    ('S14', 'kitchen', 'APPLIANCE', 7780, 2650, 500, 'B11_K-COOK_HOOD_REVIEW', '灶具/电磁炉 专用回路 TBD'),
    ('S15', 'kitchen', 'APPLIANCE', 6350, 4420, 500, 'B11_K-FRIDGE_BODY', '冰箱'),
    ('S16', 'kitchen', 'SOCKET_WET', 6600, 40, 500, 'B11_K-SINK_BOTTOM', '水槽下(净水器) 防溅'),
    ('S17', 'kitchen', 'APPLIANCE', 7780, 2100, 1850, 'B11_K-WALL-E_BASE', '吊柜内 灯带电源'),
    ('S18', 'kitchen', 'SOCKET', 5720, 1800, 1100, 'B11_K-ISLAND_ROUNDED_COUNTER', '岛台侧 PROPOSED'),
    # balcony / sunroom
    ('S19', 'service_balcony', 'SOCKET_WET', 5650, 1100, 1300, '-', '阳台备用 防溅'),
    ('S20', 'north_sunroom', 'APPLIANCE', 8650, 11140, 1300, 'SUNROOM_LAUNDRY_*', '洗衣机 防溅'),
    ('S21', 'north_sunroom', 'SOCKET', 12880, 11700, 1100, 'SUNROOM_EAST_STORAGE_COUNTER', '储物台'),
    ('S22', 'north_sunroom', 'SOCKET', 10600, 11140, 300, 'SUNROOM_SOFA_REAR_HIGH_CABINET', '一般'),
    # couple bedroom (owner) + secondary bath
    ('S23', 'couple_bedroom', 'SOCKET', 11380, 830, 700, 'HOUSE_V2_COUPLE_0_case_panel', '床头柜'),
    ('S24', 'couple_bedroom', 'SOCKET', 11380, 3340, 700, 'HOUSE_V2_COUPLE_1_case_panel', '床头柜'),
    ('S25', 'couple_bedroom', 'SOCKET', 8030, 1700, 300, 'CBM_COUPLE_CONSOLE_TOP', '电视柜'),
    ('S26', 'couple_bedroom', 'SOCKET', 8030, 2500, 300, 'CBM_COUPLE_CONSOLE_TOP', '电视柜'),
    ('S27', 'couple_bedroom', 'SOCKET_16A_AC', 11000, 230, 2200, '-', '空调'),
    ('S28', 'couple_bedroom', 'SOCKET', 8300, 4400, 300, '-', '门旁一般'),
    ('S29', 'secondary_bath', 'SOCKET_WET', 9300, 6270, 1300, 'R3_VANITY_TOP', '镜旁 防溅'),
    ('S30', 'secondary_bath', 'SOCKET_WET', 11270, 4700, 400, 'R3_WC_LATEST', '智能马桶 防溅'),
    ('S31', 'secondary_bath', 'FAN', 9800, 5200, None, '-', '排风扇(吊顶)'),
    # mother bedroom + master bath
    ('S32', 'mother_bedroom', 'SOCKET', 15270, 1040, 700, 'HOUSE_V2_MOTHER_0_case_panel', '床头柜'),
    ('S33', 'mother_bedroom', 'SOCKET', 15270, 3190, 700, 'HOUSE_V2_MOTHER_1_case_panel', '床头柜'),
    ('S34', 'mother_bedroom', 'SOCKET', 11630, 950, 1100, 'HOUSE_V2_Vanity_case_top', '梳妆台'),
    ('S35', 'mother_bedroom', 'SOCKET_16A_AC', 15270, 3650, 2200, '-', '空调'),
    ('S36', 'mother_bedroom', 'SOCKET', 11630, 3800, 300, '-', '一般'),
    ('E01', 'mother_bedroom', 'EMERGENCY_CALL', 15270, 2700, 900, 'HOUSE_V1_MOTHER_mattress', '床头紧急呼叫 PROPOSED'),
    ('S38', 'master_bath', 'SOCKET_WET', 13200, 6370, 1300, 'CBM_master_COUNTERTOP', '镜旁 防溅'),
    ('S39', 'master_bath', 'SOCKET_WET', 14420, 6370, 400, 'B11_Rectangle034_CATALOG_00_00', '智能马桶 防溅'),
    ('E02', 'master_bath', 'EMERGENCY_CALL', 14420, 5800, 900, 'B11_Rectangle034_CATALOG_00_00', '厕位旁紧急呼叫 PROPOSED'),
    ('S40', 'master_bath', 'FAN', 13900, 5100, None, '-', '排风扇(吊顶)'),
    # guest bath / guest bedroom
    ('S41', 'guest_bath', 'SOCKET_WET', 8030, 8100, 1300, 'CBM_guest_COUNTERTOP', '镜旁 防溅'),
    ('S42', 'guest_bath', 'SOCKET_WET', 8030, 9290, 400, 'B11_Rectangle008_CATALOG_00_00', '智能马桶 防溅'),
    ('S43', 'guest_bath', 'FAN', 9300, 8400, None, '-', '排风扇(吊顶)'),
    ('S44', 'guest_bedroom', 'SOCKET', 12880, 9550, 700, 'HOUSE_V2_GUEST_head_panel', '床头'),
    ('S45', 'guest_bedroom', 'SOCKET', 12880, 10300, 900, 'HOUSE_V2_Guest_desk_top', '书桌'),
    ('S46', 'guest_bedroom', 'SOCKET_16A_AC', 12880, 8300, 2200, '-', '空调'),
    ('S47', 'guest_bedroom', 'SOCKET', 12000, 8060, 300, '-', '南墙一般'),
    # study
    ('S48', 'study', 'FLOOR_BOX', 14610, 8580, 0, 'STUDY_V1_MOVABLE_DESK', '书桌地插 PROPOSED; 需地面垫层 TBD'),
    ('S49', 'study', 'SOCKET_WET', 15300, 6630, 1100, 'R3_TEA_WORKTOP_EAST', '茶水台 防溅'),
    ('S50', 'study', 'SOCKET', 13140, 10900, 400, 'STUDY_V1_DAYBED_TIMBER_TOP', '卧榻'),
    ('S51', 'study', 'SOCKET_16A_AC', 15900, 6630, 2200, '-', '空调'),
    # hallway
    ('S53', 'hallway', 'SOCKET', 10500, 7770, 300, '-', '走廊一般(吸尘)'),
    # data
    ('D01', 'living', 'DATA', 7730, 10100, 300, 'V4_Console_solid_ash_top', '电视+网络'),
    ('D02', 'couple_bedroom', 'DATA', 8030, 2100, 300, 'CBM_COUPLE_CONSOLE_TOP', '电视+网络'),
    ('D03', 'guest_bedroom', 'DATA', 12880, 10050, 900, 'HOUSE_V2_Guest_desk_top', '书桌网络'),
    ('D04', 'study', 'DATA_FLOOR', 14610, 8780, 0, 'STUDY_V1_MOVABLE_DESK', '书桌地插网络 PROPOSED'),
    ('D05', 'mother_bedroom', 'DATA', 11630, 4100, 300, '-', '备用网络 OPTIONAL'),
    ('AP1', 'living', 'AP', 5000, 9500, None, '-', '无线AP(吊顶)'),
    ('AP2', 'hallway', 'AP', 11000, 7050, None, '-', '无线AP(吊顶)'),
]

# ---- switches: (id, room, x, y, H, serves control_groups, note, status) ----
# serves: control_group strings from data/lighting_points_v2.json ('room:GROUP')
SWITCHES = [
    ('K01', 'living', 2960, 5300, 1300, ['living:BASE', 'living:TASK', 'living:SOFA_WALL', 'living:TV_WALL'], '入户场景面板', 'PROPOSED'),
    ('K02', 'living', 2930, 7600, 1300, ['living:BASE', 'living:SOFA_WALL', 'living:TV_WALL'], '沙发旁 双控', 'PROPOSED'),
    ('K03', 'kitchen', 5960, 2360, 1300, ['kitchen:BASE', 'kitchen:TASK'], '厨房', 'PROPOSED'),
    ('K04', 'kitchen', 5960, 4300, 1300, ['kitchen:BASE'], '厨房开口 双控', 'PROPOSED'),
    ('K05', 'service_balcony', 4950, 2250, 1300, ['service_balcony:BASE'], '生活阳台', 'PROPOSED'),
    ('K06', 'north_sunroom', 7960, 11650, 1300, ['north_sunroom:BASE'], '阳光房', 'PROPOSED'),
    ('K07', 'hallway', 8150, 6700, 1300, ['hallway:BASE', 'hallway:ACCENT', 'stair:ACCENT'], '走廊西 双控', 'PROPOSED'),
    ('K08', 'hallway', 12840, 7050, 1300, ['hallway:BASE', 'hallway:ACCENT', 'stair:ACCENT'], '走廊东 双控', 'PROPOSED'),
    ('K09', 'couple_bedroom', 9060, 4400, 1300, ['couple_bedroom:BASE', 'couple_bedroom:TV_WALL'], '次主卧门口 双控', 'PROPOSED'),
    ('K10', 'couple_bedroom', 11380, 1100, 900, ['couple_bedroom:BASE', 'couple_bedroom:TASK', 'couple_bedroom:NIGHT'], '床头 双控+夜灯手动', 'PROPOSED'),
    ('K11', 'couple_bedroom', 11380, 3080, 900, ['couple_bedroom:BASE', 'couple_bedroom:TASK', 'couple_bedroom:NIGHT'], '床头 双控+夜灯手动', 'PROPOSED'),
    ('K12', 'mother_bedroom', 12960, 4250, 1300, ['mother_bedroom:BASE', 'vestibule:BASE'], '主卧门口 双控', 'PROPOSED'),
    ('K13', 'mother_bedroom', 15270, 1300, 900, ['mother_bedroom:BASE', 'mother_bedroom:TASK', 'mother_bedroom:NIGHT', 'vestibule:NIGHT', 'master_bath:NIGHT'], '床头 双控+夜灯手动兜底', 'PROPOSED'),
    ('K14', 'mother_bedroom', 15270, 2930, 900, ['mother_bedroom:BASE', 'mother_bedroom:TASK', 'mother_bedroom:NIGHT', 'vestibule:NIGHT', 'master_bath:NIGHT'], '床头 双控+夜灯手动兜底', 'PROPOSED'),
    ('K15', 'vestibule', 12840, 5560, 1300, ['master_bath:BASE', 'master_bath:TASK', 'vestibule:BASE'], '主卫(门外)', 'PROPOSED'),
    ('K16', 'study', 13160, 7520, 1300, ['study:BASE', 'study:TASK'], '书房', 'PROPOSED'),
    ('K17', 'hallway', 8700, 7740, 1300, ['guest_bath:BASE', 'guest_bath:TASK'], '客卫(门外)', 'PROPOSED'),
    ('K18', 'guest_bedroom', 10920, 8060, 1300, ['guest_bedroom:BASE'], '客卧门口; 门位 H4 待定', 'TBD'),
    ('K19', 'guest_bedroom', 12880, 9350, 900, ['guest_bedroom:BASE', 'guest_bedroom:TASK'], '床头', 'PROPOSED'),
    ('K20', 'couple_bedroom', 11060, 4400, 1300, ['secondary_bath:BASE', 'secondary_bath:TASK'], '次主卫; 门位 H2 待定', 'TBD'),
]
SENSOR_GROUPS = ['mother_bedroom:NIGHT', 'vestibule:NIGHT', 'master_bath:NIGHT', 'couple_bedroom:NIGHT']

# ---- ceiling route network (schematic). Spines in plan; systems offset per spine ----
SYSTEMS = {'POWER': 0, 'DATA': 80, 'COLD': 160, 'HOT': 240}   # uniform (d, d) translation per system, away from stair/no-drop zones
SPINES = {
    'LOWER_N': [(3200, 7950), (7650, 7950)],
    'LOWER_S': [(5400, 900), (5400, 7950)],
    'SUN_LINK': [(7650, 7950), (7650, 11300)],
    'SUN': [(7650, 11300), (12500, 11300)],
    # lower -> upper through kitchen ceiling and over TV wall x7800-8000 (stair has no ceiling void)
    'STEP_LINK': [(5400, 2000), (10500, 2000)],
    'UPPER_V1': [(10500, 1200), (10500, 10300)],
    'UPPER_H': [(8150, 7300), (15500, 7300)],
    'UPPER_V2': [(12250, 2500), (12250, 7300)],
}
DEPENDS = {'LOWER_N': ['LOWER_S'], 'SUN_LINK': ['LOWER_N', 'LOWER_S'], 'SUN': ['SUN_LINK', 'LOWER_N', 'LOWER_S'],
           'STEP_LINK': ['LOWER_S'], 'UPPER_V1': ['STEP_LINK', 'LOWER_S'],
           'UPPER_H': ['UPPER_V1', 'STEP_LINK', 'LOWER_S'], 'UPPER_V2': ['UPPER_H', 'UPPER_V1', 'STEP_LINK', 'LOWER_S']}
SOURCE_LINKS = {   # source -> trunk (LOWER_S)
    'POWER': [(2950, 6800), (5400, 6800)],
    'DATA': [(2950, 7150), (5400, 7150)],
    'COLD': [(3000, 760), (3000, 900), (5400, 900)],
    'HOT': [(4000, 760), (4000, 900), (5400, 900)],
}
ROOM_SPINES = {
    'north_sunroom': ['SUN', 'SUN_LINK'], 'kitchen': ['STEP_LINK', 'LOWER_S'], 'service_balcony': ['LOWER_S'],
    'living': ['LOWER_N', 'LOWER_S', 'SUN_LINK'],
}
UPPER_SPINES = ['UPPER_H', 'UPPER_V1', 'UPPER_V2', 'STEP_LINK']
