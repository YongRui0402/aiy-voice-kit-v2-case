"""AIY-Voice-Kit外殼:殼身(五面盒)+ 頂蓋(套蓋,變體 A、B)。

執行:uv run --with build123d python aiy_case.py
產出:build/case_body.stl、.step;build/case_lid_A.stl、.step;build/case_lid_B.stl、.step

擺放就是列印的擺放(複述圖定的熱床面在 Z = 0):
  殼身  底面貼熱床、開口朝 +Z。X 向:C 面在 -X、B 面在 +X;Y 向:A 面在 -Y、D 面在 +Y
  頂蓋  頂面貼熱床、裙邊朝 +Z(倒過來印);組裝時繞 X 軸翻 180°,所以 Y 座標和殼身相反

每個尺寸的值都來自 量測/尺寸表.md,行尾註明是哪一列。
"""
import math
from pathlib import Path

import build123d as bd

# ───────────── 尺寸表:3d-print-reverse 交來的(全部 B 級) ─────────────
CARD_T = 2.0          # 尺寸表:外盒紙板厚度(卡尺實測,A 級;取代逆向那一列的估計 1.5)
BOX_D_W = 80.6        # 尺寸表:外盒 D 面寬  # B級待實測:試印後內框組件放得進殼身、左右不卡
BOX_C_W = 76.7        # 尺寸表:外盒 C 面寬  # B級待實測:試印後內框組件放得進殼身、前後不卡
BOX_D_H = 79.0        # 尺寸表:外盒 D 面高  # B級待實測:試印後蓋上頂蓋,內框與喇叭有沒有頂到

BTN_D = 24.2          # 尺寸表:外盒頂面按鈕孔直徑  # B級待實測:按鈕能否穿過、螺帽鎖得住
BTN_FROM_D = 39.0     # 尺寸表:外盒按鈕孔中心到 D 面頂折線  # B級待實測:按鈕裝上後有沒有碰到喇叭與內框

SPK_D = 14.2          # 尺寸表:外盒 D 面喇叭孔直徑(7 孔)  # B級待實測:試印後對著喇叭看孔有沒有對到振膜
SPK_PITCH = 23.8      # 尺寸表:外盒 D 面喇叭孔中心距(中央孔到周圍 6 孔)  # B級待實測:同上
SPK_Z = 38.3          # 尺寸表:外盒 D 面中央喇叭孔中心距底折線(原廠孔位;2026-11-12 起改對準喇叭中心,不用)
SPK_FROM_BD = 39.0    # 尺寸表:外盒 D 面中央喇叭孔中心距 B/D 折線(同上,不用)

# ───────────── 尺寸表:喇叭(使用者卡尺實測,A 級,2026-11-12) ─────────────
SPK_SIZE = 77.4       # 尺寸表:喇叭外框(凸點到凸點;邊朝上下擺,四邊中心有凸點)
SPK_DIAG = 92.8       # 尺寸表:喇叭外框對角(角在凸點以內,不影響外框)
SPK_DEPTH = 25.0      # 尺寸表:喇叭總厚(前框表面到磁鐵後端)
MAG_D = 40.3          # 尺寸表:喇叭磁鐵直徑
MAG_T = 6.0           # 尺寸表:喇叭磁鐵厚度
NECK_D = 36.0         # 尺寸表:盆架與磁鐵之間最細處直徑(使用者說「大概」,標 B)  # B級待實測:外層缺口卡得住、放得進

B_SLOT_L = 18.2       # 尺寸表:外盒 B 面長圓孔(長 × 寬)的長  # B級待實測:試印後對著 Bonnet 的麥克風看
B_SLOT_W = 6.4        # 尺寸表:外盒 B 面長圓孔(長 × 寬)的寬  # B級待實測:同上
B_SLOT_Z = 39.6       # 尺寸表:外盒 B 面長圓孔中心(距底折線)  # B級待實測:同上
B_SLOT_FROM_BD = 66.3  # 尺寸表:外盒 B 面長圓孔中心(距 B/D 折線)  # B級待實測:同上

SD_H = 13.5           # 尺寸表:外盒 C 面 SD Card 孔(沿面高)  # B級待實測:試印後 SD 卡能否從孔插拔
SD_W = 20.3           # 尺寸表:外盒 C 面 SD Card 孔(沿面寬)  # B級待實測:同上
SD_Z = 20.2           # 尺寸表:外盒 C 面 SD Card 孔中心(距底折線)  # B級待實測:同上
SD_FROM_CA = 16.9     # 尺寸表:外盒 C 面 SD Card 孔中心(距 C/A 折線)  # B級待實測:同上
C_SLOT_L = 18.0       # 尺寸表:外盒 C 面長圓孔(長 × 寬)的長  # B級待實測:試印後對著 Bonnet 的麥克風看
C_SLOT_W = 6.4        # 尺寸表:外盒 C 面長圓孔(長 × 寬)的寬  # B級待實測:同上
C_SLOT_Z = 40.1       # 尺寸表:外盒 C 面長圓孔中心(距底折線)  # B級待實測:同上
C_SLOT_FROM_CA = 12.9  # 尺寸表:外盒 C 面長圓孔中心(距 C/A 折線)  # B級待實測:同上

HDMI_H = 4.2          # 尺寸表:外盒 A 面 HDMI 孔(沿面高)  # B級待實測:試印後 HDMI 線插不插得進
HDMI_W = 12.4         # 尺寸表:外盒 A 面 HDMI 孔(沿面寬)  # B級待實測:同上
HDMI_Z = 17.7         # 尺寸表:外盒 A 面 HDMI 孔中心(距底折線)  # B級待實測:同上
HDMI_FROM_CA = 16.3   # 尺寸表:外盒 A 面 HDMI 孔中心(距 C/A 折線)  # B級待實測:同上
GPIO_H = 5.5          # 尺寸表:外盒 A 面 GPIO 孔(沿面高)  # B級待實測:試印後對著 Bonnet 的排針看
GPIO_W = 17.4         # 尺寸表:外盒 A 面 GPIO 孔(沿面寬)  # B級待實測:同上
GPIO_Z = 29.7         # 尺寸表:外盒 A 面 GPIO 孔中心(距底折線)  # B級待實測:同上
GPIO_FROM_CA = 17.7   # 尺寸表:外盒 A 面 GPIO 孔中心(距 C/A 折線)  # B級待實測:同上
USB_H = 4.0           # 尺寸表:外盒 A 面 Data/Power 孔(沿面高)  # B級待實測:試印後兩條 micro USB 線插不插得進
USB_W = 21.5          # 尺寸表:外盒 A 面 Data/Power 孔(沿面寬)  # B級待實測:同上
USB_Z = 17.5          # 尺寸表:外盒 A 面 Data/Power 孔中心(距底折線)  # B級待實測:同上
USB_FROM_CA = 51.6    # 尺寸表:外盒 A 面 Data/Power 孔中心(距 C/A 折線)  # B級待實測:同上
AUDIO_D = 5.0         # 尺寸表:外盒 A 面 Audio 孔直徑  # B級待實測:試印後 3.5 mm 插頭插不插得進
AUDIO_Z = 31.0        # 尺寸表:外盒 A 面 Audio 孔中心(距底折線)  # B級待實測:同上
AUDIO_FROM_CA = 58.7  # 尺寸表:外盒 A 面 Audio 孔中心(距 C/A 折線)  # B級待實測:同上

# ───────────── 公差:依 Bambu Lab X2D 實測(2026-11-12),換印表機時先改這一段 ─────────────
# 開孔的值量的是原廠外盒上既有的孔(掃描描圖)→ 只補償孔印小(原始檔規範 Rule 27),不再加穿過的間隙
# fit_clearance_mm.snug 是 null → reference_b.hole_clearance_mm.grip
HOLE_GRIP = 0.2       # 尺寸表:開孔公差(只補償孔印小)  # B級待實測:接頭與按鈕是否穿過開孔、不卡
# xy_outer_offset_mm = -0.2(實測):殼身外輪廓會印小 0.2,頂蓋凹槽(內輪廓)印小多少沒有實測
# → 設計間隙往小取,一片 0.0、一片 0.3;印出來的實際間隙約等於設計值 + 0.2 − 凹槽印小的量
LID_GAP_VARIANTS = {"A": 0.0, "B": 0.3}   # 尺寸表:頂蓋套合間隙(變體 A、B,兩側合計)  # B級待實測:哪一片套得上又不會自己鬆脫
# self_support_chamfer_deg = 45(實測);overhang_max_from_vertical_deg = 45(實測)
TEAR_DEG = 45.0       # 尺寸表:側壁圓孔上緣尖頂的角度

# ───────────── 自定(層高 0.20、外牆線寬 0.42) ─────────────
WALL = 1.68           # 尺寸表:側壁厚度(自定)
FLOOR = 1.2           # 尺寸表:殼身底板厚度(自定)
LID_T = 1.6           # 尺寸表:頂蓋頂板厚度(自定)
SKIRT_T = 1.26        # 尺寸表:頂蓋裙邊厚度(自定)
SKIRT_H = 8.0         # 尺寸表:頂蓋裙邊高度(自定:0.20 × 40 層;加深才有彈性撐過卡扣凸條)
FRAME_GAP = 0.5       # 尺寸表:內框四周餘隙(每側)(自定)
SPK_GAP = 0.4         # 尺寸表:喇叭外框四周餘隙(每側)(自定)
EDGE_CHAMFER = 0.4    # 尺寸表:底部外緣倒角(自定)
MARK_SIZE = 8.0       # 尺寸表:變體記號字高(自定)
MARK_DEPTH = 0.4      # 尺寸表:變體記號刻入深度(自定)
MARK_INSET = 10.0     # 尺寸表:變體記號中心到頂蓋內緣(D 面側)(自定)
SNAP_H = 0.4          # 尺寸表:卡扣凸條凸出殼身外壁的高度(自定)  # B級待實測:壓得進去、卡得住、撬得開
SNAP_FROM_TOP = 4.0   # 尺寸表:卡扣凸條中心到殼身上緣(自定:裙邊高度的一半)
SNAP_L = 30.0         # 尺寸表:每一面卡扣凸條的長度(自定:只做每面中段,轉角不做,裙邊才彎得動)
SNAP_GROOVE_EXTRA = 0.1   # 尺寸表:頂蓋凹槽比凸條深多少(自定)
SKIRT_LEAD = 0.6      # 尺寸表:裙邊開口內緣的導角(自定:壓蓋子時先滑上凸條)
USB_RIB = 1.26        # 尺寸表:Data/Power 孔中間的肋寬(自定:0.42 × 3 條;≥ min_wall_mm 0.8)

# ───────────── 由主尺寸算出來的 ─────────────
IN_X = max(BOX_D_W - 2 * CARD_T + 2 * FRAME_GAP, SPK_SIZE + 2 * SPK_GAP)   # 內部 X:紙盒內部寬加餘隙;喇叭 77.4 放不下時以喇叭為準
IN_Y = BOX_C_W - 2 * CARD_T + 2 * FRAME_GAP     # 內部 Y:紙盒內部深(C 面寬扣兩層紙板)加兩側餘隙
IN_Z = max(BOX_D_H - 2 * CARD_T, round((SPK_SIZE + SPK_GAP) / 0.2 + 0.4999) * 0.2)   # 內部淨高:紙盒內部高;喇叭邊朝上下坐在殼底,77.4 放不下時以喇叭為準(取 0.2 的倍數)
OUT_X = IN_X + 2 * WALL
OUT_Y = IN_Y + 2 * WALL
BODY_H = FLOOR + IN_Z
SPK_CX = 0.0                                    # 喇叭中心 X:左右置中
SPK_CZ = FLOOR + SPK_SIZE / 2                   # 喇叭中心 Z:邊朝上下、坐在殼底
BODY_FILLET = WALL                              # 殼身立邊圓角:等於側壁厚度,轉角處壁厚不變薄
LID_FILLET = SKIRT_T                            # 頂蓋立邊圓角:等於裙邊厚度
THROUGH = WALL * 3                              # 不是零件的尺寸:切除工具的長度,前後都超出側壁

BOTTOM = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)


# 折線座標 → 模型座標(紙盒內壁 = 折線往內一層紙板;紙盒內壁再往外一個餘隙才是殼身內壁)
def x_from_ca(v):      # A 面上距 C/A 折線 v(C 面在 -X)
    return -IN_X / 2 + FRAME_GAP + (v - CARD_T)


def x_from_bd(v):      # D 面上距 B/D 折線 v(B 面在 +X)
    return IN_X / 2 - FRAME_GAP - (v - CARD_T)


def y_from_ca(v):      # C 面上距 C/A 折線 v(A 面在 -Y)
    return -IN_Y / 2 + FRAME_GAP + (v - CARD_T)


def y_from_bd(v):      # B 面與頂面上距 B/D 折線(D 面頂折線)v(D 面在 +Y)
    return IN_Y / 2 - FRAME_GAP - (v - CARD_T)


def z_from_bottom(v):  # 距底折線 v
    return FLOOR + (v - CARD_T)


# 側壁上的開孔輪廓(局部座標:u 水平、v = 列印的 Z)
def peak(r, v0=0.0):
    """半徑 r 的圓弧頂上加一個尖頂,斜面與水平夾 TEAR_DEG,不留超過門檻角的懸垂。"""
    a = math.radians(90 - TEAR_DEG)
    return bd.Polygon((r * math.cos(a), v0 + r * math.sin(a)), (0, v0 + r / math.cos(math.radians(TEAR_DEG))),
                      (-r * math.cos(a), v0 + r * math.sin(a)), align=None)


def round_hole(d):
    r = (d + HOLE_GRIP) / 2
    return bd.Circle(r) + peak(r)


def round_hole_plain(d):
    """小圓孔(耳機孔):頂端懸空短,不做尖頂。"""
    return bd.Circle((d + HOLE_GRIP) / 2)


def hex_hole(d):
    """六邊形孔,平邊朝上:外接圓直徑 = 原孔徑 + 公差;兩側斜邊與水平夾 60°,頂邊是一段 d/2 的短橋接,免支撐。
    (尖角朝上時頂端兩條斜邊離水平只有 30°,超過 overhang_max_from_vertical_deg 45,不用)"""
    return bd.RegularPolygon((d + HOLE_GRIP) / 2, 6, rotation=0)


def snap_rod(length, protrude):
    """卡扣凸條(或凹槽)的切面是 45° 菱形的一半:正方形轉 45°,中心放在牆面上。"""
    s = protrude * math.sqrt(2)
    return bd.Rot(45, 0, 0) * bd.Box(length, s, s)


def slot_hole(length, width):
    full_l, r = length + HOLE_GRIP, (width + HOLE_GRIP) / 2
    return bd.SlotOverall(full_l, 2 * r, rotation=90) + peak(r, full_l / 2 - r)


def rect_hole(w, h):
    return bd.Rectangle(w + HOLE_GRIP, h + HOLE_GRIP)


def cut_on_y_wall(profile, x, y_wall, z):      # A 面、D 面:輪廓在 XZ 平面,沿 Y 切穿側壁
    return bd.Pos(x, y_wall, z) * bd.extrude(bd.Plane.XZ * profile, amount=THROUGH / 2, both=True)


def cut_on_x_wall(profile, x_wall, y, z):      # C 面、B 面:輪廓在 YZ 平面,沿 X 切穿側壁
    return bd.Pos(x_wall, y, z) * bd.extrude(bd.Plane.YZ * profile, amount=THROUGH / 2, both=True)


def outer_vertical_edges(part, half_x, half_y):
    tol = 1e-4
    return [e for e in part.edges().filter_by(bd.Axis.Z)
            if abs(abs(e.center().X) - half_x) < tol and abs(abs(e.center().Y) - half_y) < tol]


def make_body():
    # 1. 主體與挖空(切除,不抽殼)
    body = bd.Box(OUT_X, OUT_Y, BODY_H, align=BOTTOM)
    body -= bd.Pos(0, 0, FLOOR) * bd.Box(IN_X, IN_Y, IN_Z + THROUGH, align=BOTTOM)

    # 2. 開孔
    y_a, y_d = -(IN_Y + WALL) / 2, (IN_Y + WALL) / 2      # A、D 面側壁的中心面
    x_c, x_b = -(IN_X + WALL) / 2, (IN_X + WALL) / 2      # C、B 面側壁的中心面
    # A 面:HDMI、GPIO、Data/Power(方孔,上緣橋接)、Audio(圓孔,尖頂)
    body -= cut_on_y_wall(rect_hole(HDMI_W, HDMI_H), x_from_ca(HDMI_FROM_CA), y_a, z_from_bottom(HDMI_Z))
    body -= cut_on_y_wall(rect_hole(GPIO_W, GPIO_H), x_from_ca(GPIO_FROM_CA), y_a, z_from_bottom(GPIO_Z))
    # Data/Power:原廠是一個 21.5 寬的長方孔;上緣橋接超過 bridge_max_mm 20(實測),中間留一道肋拆成兩孔
    usb_half_w = (USB_W + HOLE_GRIP - USB_RIB) / 2          # 每一孔的寬:整孔寬扣掉肋再對半
    usb_off = (usb_half_w + USB_RIB) / 2                    # 每一孔中心離原孔中心
    for s in (-1, 1):
        body -= cut_on_y_wall(bd.Rectangle(usb_half_w, USB_H + HOLE_GRIP), x_from_ca(USB_FROM_CA) + s * usb_off,
                              y_a, z_from_bottom(USB_Z))
    body -= cut_on_y_wall(round_hole_plain(AUDIO_D), x_from_ca(AUDIO_FROM_CA), y_a, z_from_bottom(AUDIO_Z))
    # D 面:喇叭孔,中央 1 個 + 周圍 6 個;從上到下 1-2-1-2-1(中間一直排 3 個,和原廠紙盒同排法,使用者 2026-11-12 決定),
    # 六邊形平邊朝上:這個排法剛好是平邊朝上六邊形的蜂巢排列
    spk = bd.Pos(SPK_CX, 0, SPK_CZ)                         # 對準喇叭中心(喇叭坐在殼底、左右置中)
    ring = bd.Plane.XZ * bd.PolarLocations(SPK_PITCH, 6, start_angle=90, rotate=False) * hex_hole(SPK_D)   # rotate=False:平邊一律朝 +Z
    spk_profile = bd.Plane.XZ * hex_hole(SPK_D) + ring
    body -= bd.Pos(0, y_d, 0) * spk * bd.extrude(spk_profile, amount=THROUGH / 2, both=True)
    # C 面:SD Card 孔與長圓孔;B 面:長圓孔
    body -= cut_on_x_wall(rect_hole(SD_W, SD_H), x_c, y_from_ca(SD_FROM_CA), z_from_bottom(SD_Z))
    body -= cut_on_x_wall(slot_hole(C_SLOT_L, C_SLOT_W), x_c, y_from_ca(C_SLOT_FROM_CA), z_from_bottom(C_SLOT_Z))
    body -= cut_on_x_wall(slot_hole(B_SLOT_L, B_SLOT_W), x_b, y_from_bd(B_SLOT_FROM_BD), z_from_bottom(B_SLOT_Z))

    # 3. 修飾:立邊圓角(XY 平面)、底面外緣倒角(Z 向轉折)
    body = bd.fillet(outer_vertical_edges(body, OUT_X / 2, OUT_Y / 2), BODY_FILLET)
    body = bd.chamfer(body.edges().group_by(bd.Axis.Z)[0], EDGE_CHAMFER)

    # 4. 卡扣凸條:四面外壁中段各一條(新特徵吃進母體:菱形一半埋在牆裡)
    z = BODY_H - SNAP_FROM_TOP
    for (x, y, rot) in ((0, -OUT_Y / 2, 0), (0, OUT_Y / 2, 0), (-OUT_X / 2, 0, 90), (OUT_X / 2, 0, 90)):
        body += bd.Pos(x, y, z) * bd.Rot(0, 0, rot) * snap_rod(SNAP_L, SNAP_H)
    return body


def make_lid(mark, gap):
    """頂蓋,倒過來印:頂面在 Z = 0、裙邊朝 +Z。組裝座標的 Y 在這裡要反號。"""
    pocket_x, pocket_y = OUT_X + gap, OUT_Y + gap
    lid_x, lid_y = pocket_x + 2 * SKIRT_T, pocket_y + 2 * SKIRT_T

    # 1. 主體與套住殼身的凹槽(切除)
    lid = bd.Box(lid_x, lid_y, LID_T + SKIRT_H, align=BOTTOM)
    lid -= bd.Pos(0, 0, LID_T) * bd.Box(pocket_x, pocket_y, SKIRT_H + THROUGH, align=BOTTOM)

    # 2. 按鈕孔(圓在 XY 平面)與變體記號(刻在內面靠 D 面的一側)
    btn_r = (BTN_D + HOLE_GRIP) / 2
    lid -= bd.Pos(0, -y_from_bd(BTN_FROM_D), 0) * bd.Cylinder(btn_r, LID_T + THROUGH)
    text = bd.extrude(bd.Text(mark, MARK_SIZE), amount=MARK_DEPTH + THROUGH)
    lid -= bd.Pos(0, -(IN_Y / 2 - MARK_INSET), LID_T - MARK_DEPTH) * text

    # 2b. 卡扣凹槽:對著殼身的凸條(倒過來印,凸條中心在頂板內面往上 SNAP_FROM_TOP)與裙邊開口導角
    z = LID_T + SNAP_FROM_TOP
    for (x, y, rot) in ((0, -pocket_y / 2, 0), (0, pocket_y / 2, 0), (-pocket_x / 2, 0, 90), (pocket_x / 2, 0, 90)):
        lid -= bd.Pos(x, y, z) * bd.Rot(0, 0, rot) * snap_rod(SNAP_L + 1.0, SNAP_H + SNAP_GROOVE_EXTRA)
    lead = bd.extrude(bd.Rectangle(pocket_x + 2 * SKIRT_LEAD, pocket_y + 2 * SKIRT_LEAD), amount=-SKIRT_LEAD, taper=45)
    lid -= bd.Pos(0, 0, LID_T + SKIRT_H) * lead

    # 3. 修飾:立邊圓角(XY 平面)、頂面外緣倒角(Z 向轉折;按鈕孔的邊不動)
    lid = bd.fillet(outer_vertical_edges(lid, lid_x / 2, lid_y / 2), LID_FILLET)
    rim = [e for e in lid.edges().group_by(bd.Axis.Z)[0]
           if not (e.geom_type == bd.GeomType.CIRCLE and abs(e.radius - btn_r) < 1e-6)]
    lid = bd.chamfer(rim, EDGE_CHAMFER)
    return lid


if __name__ == "__main__":
    build = Path(__file__).parent / "build"
    build.mkdir(exist_ok=True)
    parts = {"case_body": make_body()}
    for mark, gap in LID_GAP_VARIANTS.items():
        parts[f"case_lid_{mark}"] = make_lid(mark, gap)
    for name, part in parts.items():
        bd.export_stl(part, str(build / f"{name}.stl"))
        bd.export_step(part, str(build / f"{name}.step"))
        size = part.bounding_box().size
        print(f"{name}: {size.X:.2f} × {size.Y:.2f} × {size.Z:.2f} mm, 體積 {part.volume / 1000:.1f} cm³")
