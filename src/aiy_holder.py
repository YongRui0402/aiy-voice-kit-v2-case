"""AIY-Voice-Kit外殼:內部支架(取代原廠紙板內框;外形不超出紙架,兩種都放得進同一個殼身)。

執行:uv run --with build123d python aiy_holder.py
產出:build/holder.stl、build/holder.step(列印擺法:後牆背面貼熱床、立著印)

結構照 量測/內框摺回立體.py 摺回的紙架(使用者 2026-11-12 確認):
  底板     平放在殼身底板上,前緣朝 A 面
  後牆     紙架是雙層牆(使用者 2026-11-12 確認讀法 A):兩層中間的空隙放磁鐵;外層的 U 形缺口卡在盆架與磁鐵之間的頸部,
           內層(靠 A 面)是整片,擋住磁鐵。位置由喇叭實測決定:喇叭前框貼 D 面,磁鐵在離 D 面 19~25。
           塑膠版兩層之間填實,只留磁鐵空腔;空腔靠 A 面那端 45° 收窄約 2 擋住磁鐵外圈,中間直接開穿後牆正面
           (第三版的梯形罩封頂撞到頂蓋按鈕,第四版拿掉;立著印時開穿的空腔沒有頂,不懸空)
  左右側牆 位置照紙架側翼(兩條直折線相距 52.7,掃描是紙板外側,左右鏡射);
           各兩條橫向切縫,Pi 與 Bonnet 從 A 面那側穿進去,板子兩端伸出牆外(麥克風、SD 卡露在外面),
           切縫 D 端封住當擋塊;側牆和紙架側翼一樣高到接近頂蓋

座標:make_holder() 回傳組裝座標(同 aiy_case.py:C 面 -X、A 面 -Y;Z 從殼身底板上表面算)。
匯出的 STL 轉成列印擺法 print_pose():後牆背面在 Z = 0。
為什麼立著印:板子要穿過側牆 30 長的切縫;底板朝下印時切縫上面的牆懸空(30 超過 bridge_max_mm 20,
A 端又是開口);立著印時切縫是直立的、開口朝上,不用支撐。
"""
import math
from pathlib import Path

import build123d as bd

from aiy_case import (BOX_C_W, CARD_T, EDGE_CHAMFER, FLOOR, HDMI_FROM_CA, HDMI_Z, IN_Y, MAG_D, MAG_T, NECK_D,
                      SPK_CX, SPK_CZ, SPK_DEPTH, x_from_ca, z_from_bottom)

# ───────────── 尺寸表:紙架掃描描圖(voiceAIY_01)摺回立體得來的(B 級) ─────────────
BASE_W = 77.0         # 尺寸表:內框底板自由邊寬(卡尺實測,A 級)
# 側翼輪廓(量測/輪廓-內框.svg 摺回後,u = 離 A 端、z = 離側翼下緣;使用者 2026-11-12 要照紙架做)
WING_TOP = 69.18      # 尺寸表:內框側翼頂
WING_SLANT = ((0.0, 48.26), (4.40, 67.40), (5.50, 68.58))   # 尺寸表:側翼 A 端上角斜切的三個點
WING_STEP_U = 43.18   # 尺寸表:側翼靠後牆那段降低的起點
WING_LOW = 53.5       # 尺寸表:側翼靠後牆那段的高度(疊圖讀值)
SLIT_LOW_Z = 9.55     # 尺寸表:側翼下切縫的下緣(Pi)
MOUTH_U = 22.69       # 尺寸表:側翼 A 端大開口的深度(之後只剩兩條切縫)
MOUTH_RISE = (12.87, 9.23, 4.66)   # 尺寸表:開口上緣從 u 12.87 開始往 A 端升高,到 u 9.23 升高 4.66
OVAL_U = (6.94, 17.02)  # 尺寸表:側翼橢圓孔(u 範圍)
OVAL_Z = (33.70, 49.96)  # 尺寸表:側翼橢圓孔(z 範圍)
FOLD_L, FOLD_R = 50.80, 103.46   # 尺寸表:側翼兩條直折線在展開圖上的 x(相距 52.7)
FOLD_CX = (33.87 + 111.34) / 2   # 尺寸表:底板與後牆在展開圖上的左右中心
PCB_PITCH = 12.6      # 尺寸表:側翼兩條橫槽的間距 = Pi 底面到 Bonnet 底面(摺回立體換算)  # B級待實測:Bonnet 穿得進上層切縫

# ───────────── 尺寸表:Pi Zero W(元件庫/Raspberry-Pi-Zero-W.md,B 級) ─────────────
PCB_W, PCB_D, PCB_T = 65.0, 30.0, 1.6      # 板長、板寬、板厚
PI_HDMI_X = 12.4      # 尺寸表:Pi Zero W mini HDMI 中心距 SD 卡那一端(規格書)
PI_HDMI_ABOVE = 3.2   # 尺寸表:mini HDMI 中心距板底(板厚 1.6 + 接頭半高 1.6,估計)  # B級待實測:HDMI 對得到 A 面開孔
PCB_FROM_A = 2.0      # 尺寸表:板子前緣(接頭那一邊)到殼身 A 面內壁(估計,接頭比板緣凸出約 1)
BOARD_PLAY = 3.4      # 尺寸表:第三版板子在殼裡前後可以晃的量(使用者實測,回饋單 2026-11-12-2 PF-03;電源插頭插上後鬆)
BOARD_PLAY_LEFT = 0.6  # 尺寸表:第四版要留的前後晃動(自定:止擋往 A 面移 BOARD_PLAY − 這個值;前面靠接頭頂到 A 面內壁擋住)  # B級待實測:插頭插得緊、整組還放得進殼身

# ───────────── 自定(層高 0.20、線寬 0.42) ─────────────
LAYER_H = 0.20        # 層高(專案 README:2026-11-12 使用者決定)
# 支架立著印:組裝的前後(Y)是列印的 Z,取層高的倍數;組裝的上下(Z)與左右(X)是列印的 XY,取線寬 0.42 的倍數
BASE_T = 2.1          # 尺寸表:支架底板厚度(自定:立著印時是 XY 方向的牆,0.42 × 5 條)
SIDE_T = 1.68         # 尺寸表:側牆厚度(自定:0.42 × 4 條)
PCB_GAP = 0.2         # 尺寸表:切縫上下各留的間隙(自定;規格與限制.md fit_clearance_mm.snug 是 null → reference_b.hole_clearance_mm.grip)  # B級待實測:板子穿得進去又不晃
COMP_CLEAR = 1.5      # 尺寸表:Bonnet 切縫上下各再留的元件淨空(自定:第三版側牆刮掉 Bonnet 上一顆 SMD 電阻,使用者量不到元件高,預設 1.5;Bonnet 靠排針固定在 Pi 上,不必靠切縫夾)  # B級待實測:Bonnet 穿過側牆不刮到元件
SLIT_STOP = 0.3       # 尺寸表:板子後緣到切縫 D 端的間隙(自定)
OUTER_T = 1.6         # 尺寸表:後牆外層厚度(自定:立著印時是 Z 向,0.20 × 8 層;要放得進頸部,紙板是 2.0)
MAG_CLEAR = 0.8       # 尺寸表:磁鐵空腔比磁鐵寬多少(自定:每邊 0.4,斜面起點才落在層高的倍數上)
MAG_GAP = 0.2         # 尺寸表:磁鐵前後到外層、內層各留的間隙(自定)  # B級待實測:喇叭裝上去不晃
NECK_GAP = 0.4        # 尺寸表:外層缺口比頸部寬多少(自定;紙板缺口 35.3 比頸部小,靠紙板撐開夾住,塑膠撐不開)
LIP_LAND = 0.6        # 尺寸表:擋磁鐵的唇收完 45° 後到後牆正面的直段(自定:0.20 × 3 層;沒有這段,唇口是 45° 刀口,壁厚趨近 0)
WALL_TOP_ABOVE_MAG = 1.0   # 尺寸表:後牆頂在磁鐵上緣上方多少(自定;紙架後牆含被蓋住的反折段,照片估約 62)

# ───────────── 由主尺寸算出來的(組裝座標) ─────────────
CARTON_IN_D = BOX_C_W - 2 * CARD_T            # 紙盒內部深(A 到 D):紙架在紙盒裡就是頂著這兩面
MAG_BACK_Y = IN_Y / 2 - SPK_DEPTH              # 磁鐵後端:喇叭前框貼 D 面內壁
MAG_FRONT_Y = MAG_BACK_Y + MAG_T              # 磁鐵前緣(靠盆架)
Y_BACK = MAG_FRONT_Y + MAG_GAP + OUTER_T      # 外層背面(朝喇叭盆架那一面)
MAG_STOP = Y_BACK - (MAG_BACK_Y - MAG_GAP)    # 外層背面到內層(擋磁鐵那一面)
LIP_END = MAG_STOP + OUTER_T                  # 45° 斜面收完的位置(離外層背面)
WALL_GAP = LIP_END + LIP_LAND                 # 後牆厚度(外層背面到內層正面)
Y_WALL_FRONT = Y_BACK - WALL_GAP              # 後牆正面
BASE_L = math.floor((Y_BACK - (-IN_Y / 2 + (IN_Y - CARTON_IN_D))) / LAYER_H + 1e-9) * LAYER_H   # 底板長 = 支架列印高度:到離 A 面內壁 1.0 為止,取層高的倍數(紙架是 60.5)
Y_FRONT = Y_BACK - BASE_L                     # 底板前緣
NOTCH_W = NECK_D + NECK_GAP                   # 外層 U 缺口寬
NOTCH_R = NOTCH_W / 2
NOTCH_X = SPK_CX
NOTCH_C = SPK_CZ - FLOOR                      # 缺口圓弧中心 = 喇叭中心(支架座標,Z 從殼底上表面算)
NOTCH_BOTTOM = NOTCH_C - NOTCH_R
POCKET_BOTTOM = NOTCH_C - (MAG_D + MAG_CLEAR) / 2
WALL_H = NOTCH_C + MAG_D / 2 + WALL_TOP_ABOVE_MAG
WALL_L_X = -(FOLD_R - FOLD_CX)                # 左側牆中心:展開圖右邊那條折線,鏡射(掃描是紙板外側)
WALL_R_X = -(FOLD_L - FOLD_CX)                # 右側牆中心
PCB_X0 = x_from_ca(HDMI_FROM_CA) - PI_HDMI_X  # Pi 靠 C 面的短邊:由 A 面 HDMI 孔反推
PCB_X1 = PCB_X0 + PCB_W
PCB_Y0 = -IN_Y / 2 + PCB_FROM_A - (BOARD_PLAY - BOARD_PLAY_LEFT)   # 照第三版實測修正;PCB_FROM_A 的估計和實物差了這一段,原因沒查(接頭凸出量、喇叭與支架的餘隙都可能)
PCB_Y1 = PCB_Y0 + PCB_D
PI_Z = z_from_bottom(HDMI_Z) - FLOOR - PI_HDMI_ABOVE      # Pi 底面:由 A 面 HDMI 孔高度反推
BONNET_Z = PI_Z + PCB_PITCH
SLIT_H = PCB_T + 2 * PCB_GAP                  # 切縫高度
POCKET_W = MAG_D + MAG_CLEAR                  # 磁鐵空腔寬
TAPER_START = MAG_STOP - (POCKET_W - MAG_D) / 2       # 斜面起點:讓磁鐵外圈剛好在 MAG_STOP 頂到斜面
LIP_OPEN = POCKET_W - 2 * (LIP_END - TAPER_START)      # 斜面收完時的開口寬(擋磁鐵的唇 = 斜面起點到 LIP_END,再直走 LIP_LAND 到正面)
MAG_HOLD = (MAG_D - LIP_OPEN) / 2                     # 唇擋住的磁鐵外圈寬(每邊)


def box(x0, x1, y0, y1, z0, z1):
    return bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * bd.Box(x1 - x0, y1 - y0, z1 - z0)


Z_OFF = (PI_Z - PCB_GAP) - SLIT_LOW_Z          # 紙架側翼 z → 支架 z:用下切縫對齊(紙架側翼站在約 2 厚的底板紙上)
WING_H = WING_TOP + Z_OFF                     # 支架側牆高


def side_wall_profile():
    """側牆輪廓(u, z):A 端上角斜切;靠後牆那段降低,高低交界改成 45° 斜坡(立著印時才不懸空)。"""
    low = WING_LOW + Z_OFF
    u_low = WING_STEP_U + (WING_H - low) / 2      # 45° 斜坡以紙架的階梯位置為中心
    pts = [(0.0, 0.0), (BASE_L, 0.0), (BASE_L, low), (u_low, low), (u_low - (WING_H - low), WING_H)]
    pts += [(u, z + Z_OFF) for u, z in reversed(WING_SLANT)]
    return pts


def side_wall_cuts():
    """側壁要切掉的(u, z)輪廓:A 端大開口(板子前段從這裡過)與橢圓孔。"""
    zb, zt = PI_Z - PCB_GAP, BONNET_Z - PCB_GAP + SLIT_H        # 開口上下緣 = 下切縫下緣、上切縫上緣
    u1, u2, rise = MOUTH_RISE
    mouth = [(-1.0, zb), (MOUTH_U, zb), (MOUTH_U, zt), (u1, zt), (u2, zt + rise), (-1.0, zt + rise)]
    oval_c = ((OVAL_U[0] + OVAL_U[1]) / 2, (OVAL_Z[0] + OVAL_Z[1]) / 2 + Z_OFF)
    return mouth, oval_c, (OVAL_Z[1] - OVAL_Z[0], OVAL_U[1] - OVAL_U[0])


def on_wall(x, pts):
    """把側牆平面上的 (u, z) 多邊形放到 X = x 的牆上,沿 X 拉成牆厚(多切 1)。"""
    face = bd.Plane.YZ * bd.Polygon(*[(Y_FRONT + u, z) for u, z in pts], align=None)
    return bd.Pos(x - SIDE_T / 2 - 0.5, 0, 0) * bd.extrude(face, amount=SIDE_T + 1, dir=(1, 0, 0))


def make_holder():
    """組裝座標的支架。"""
    # 1. 主體:底板、實心後牆、左右側牆(側牆一路到後牆背面,立著印時下緣才貼得到熱床)
    holder = box(-BASE_W / 2, BASE_W / 2, Y_FRONT, Y_BACK, 0, BASE_T)
    holder += box(-BASE_W / 2, BASE_W / 2, Y_WALL_FRONT, Y_BACK, 0, WALL_H)
    for x in (WALL_L_X, WALL_R_X):
        face = bd.Plane.YZ * bd.Polygon(*[(Y_FRONT + u, z) for u, z in side_wall_profile()], align=None)
        holder += bd.Pos(x - SIDE_T / 2, 0, 0) * bd.extrude(face, amount=SIDE_T, dir=(1, 0, 0))


    # 2. 切除:外層的 U 形缺口、磁鐵空腔、兩片側牆的兩條切縫(A 端開口、D 端封住)
    notch = bd.Pos(NOTCH_X, Y_BACK - OUTER_T / 2, NOTCH_C) * bd.Rot(90, 0, 0) * bd.Cylinder(NOTCH_R, OUTER_T + 2)
    notch += box(NOTCH_X - NOTCH_W / 2, NOTCH_X + NOTCH_W / 2, Y_BACK - OUTER_T - 0.1, Y_BACK + 1, NOTCH_C, WALL_H + 1)
    holder -= notch
    # 磁鐵空腔:外層後面就是 POCKET_W 寬(比缺口寬,立著印時是懸在外層上面的空間,不懸空),
    # 保持到斜面起點,45° 收到 LIP_END(擋住磁鐵外圈),再以 LIP_OPEN 寬直直開穿正面;從磁鐵下緣一路開到頂(U 形開口朝上,喇叭從上面放進去)
    w_p, w_o = POCKET_W / 2, LIP_OPEN / 2
    d1 = OUTER_T
    pocket = bd.Polygon((NOTCH_X - w_p, Y_BACK - d1), (NOTCH_X + w_p, Y_BACK - d1), (NOTCH_X + w_p, Y_BACK - TAPER_START),
                        (NOTCH_X + w_o, Y_BACK - LIP_END), (NOTCH_X + w_o, Y_WALL_FRONT - 1), (NOTCH_X - w_o, Y_WALL_FRONT - 1),
                        (NOTCH_X - w_o, Y_BACK - LIP_END), (NOTCH_X - w_p, Y_BACK - TAPER_START), align=None)
    holder -= bd.Pos(0, 0, POCKET_BOTTOM) * bd.extrude(pocket, amount=WALL_H - POCKET_BOTTOM + 1, dir=(0, 0, 1))
    mouth, oval_c, (oval_l, oval_w) = side_wall_cuts()
    for x in (WALL_L_X, WALL_R_X):
        holder -= on_wall(x, mouth)
        oval = bd.Plane.YZ * (bd.Pos(Y_FRONT + oval_c[0], oval_c[1]) * bd.SlotOverall(oval_l, oval_w, rotation=90))
        holder -= bd.Pos(x - SIDE_T / 2 - 0.5, 0, 0) * bd.extrude(oval, amount=SIDE_T + 1, dir=(1, 0, 0))
        for z, clear in ((PI_Z, 0.0), (BONNET_Z, COMP_CLEAR)):
            holder -= box(x - SIDE_T, x + SIDE_T, Y_FRONT - 1, PCB_Y1 + SLIT_STOP, z - PCB_GAP - clear, z - PCB_GAP + SLIT_H + clear)
    return holder


def print_pose(part):
    """轉成列印擺法:後牆背面(Y = Y_BACK)貼熱床。組裝的 Z 變成列印的 +Y,組裝的 -Y 變成列印的 +Z。"""
    part = bd.Pos(0, 0, Y_BACK) * bd.Rot(-90, 0, 0) * part
    # 修飾:貼熱床那一面的外緣倒角(Z 向轉折)
    return bd.chamfer(part.edges().group_by(bd.Axis.Z)[0], EDGE_CHAMFER)


if __name__ == "__main__":
    build = Path(__file__).parent / "build"
    build.mkdir(exist_ok=True)
    holder = print_pose(make_holder())
    bd.export_stl(holder, str(build / "holder.stl"))
    bd.export_step(holder, str(build / "holder.step"))
    size = holder.bounding_box().size
    print(f"holder(列印擺法): {size.X:.2f} × {size.Y:.2f} × {size.Z:.2f} mm, 體積 {holder.volume / 1000:.1f} cm³")
    print(f"  Pi X {PCB_X0:.2f}~{PCB_X1:.2f}、Y {PCB_Y0:.2f}~{PCB_Y1:.2f}、底面 Z {PI_Z:.2f};Bonnet 底面 Z {BONNET_Z:.2f}")
    print(f"  側牆中心 X {WALL_L_X:.2f}、{WALL_R_X:.2f}(相距 {WALL_R_X - WALL_L_X:.2f});板子伸出牆外 {WALL_L_X - SIDE_T / 2 - PCB_X0:.2f}、{PCB_X1 - WALL_R_X - SIDE_T / 2:.2f}")
    print(f"  磁鐵空腔寬 {POCKET_W:.1f}、內層擋磁鐵處離後牆背面 {MAG_STOP:.2f};正面開口寬 {LIP_OPEN:.2f}(每邊擋住磁鐵外圈 {MAG_HOLD:.2f})")
    print(f"  Bonnet 切縫 Z {BONNET_Z - PCB_GAP - COMP_CLEAR:.2f}~{BONNET_Z - PCB_GAP + SLIT_H + COMP_CLEAR:.2f}(高 {SLIT_H + 2 * COMP_CLEAR:.2f});Pi 切縫高 {SLIT_H:.2f}")
    print(f"  外層背面 Y {Y_BACK:.2f}(到 D 面內壁 {IN_Y / 2 - Y_BACK:.2f});磁鐵 Y {MAG_BACK_Y:.2f}~{MAG_FRONT_Y:.2f};底板長 {BASE_L:.2f};後牆高 {WALL_H:.2f}")
    print(f"  U 缺口寬 {NOTCH_W:.1f}、中心 Z {NOTCH_C:.2f}、底 Z {NOTCH_BOTTOM:.2f};磁鐵空腔底 Z {POCKET_BOTTOM:.2f}")
