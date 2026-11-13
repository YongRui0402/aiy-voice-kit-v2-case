"""組裝 STEP:殼身、支架、頂蓋放在組裝位置(頂蓋往上抬開 30 mm),加上示意的 Pi、Bonnet、喇叭,給 FreeCAD 看。

執行:uv run python src/assembly.py  →  src/build/assembly.step、assembly_exploded.step
零件直接呼叫 aiy_case.py、aiy_holder.py 的建模函式,不讀匯出檔;每個零件是組裝裡的一個物件,有名稱與顏色。
名稱用英文:STEP 寫中文會變亂碼(2026-11-12 FreeCAD 開啟時看到)。
"""
import sys
from pathlib import Path

import build123d as bd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from aiy_case import BODY_H, FLOOR, IN_Y, LID_GAP_VARIANTS, LID_T, make_body, make_lid  # noqa: E402
from aiy_holder import BONNET_Z, PCB_X0, PCB_X1, PCB_Y0, PCB_Y1, PI_Z, make_holder  # noqa: E402

LIFT = 30.0   # 頂蓋抬開的距離


def named(shape, label, rgb):
    shape.label = label
    shape.color = bd.Color(*rgb)
    return shape


def board(z, label, rgb):
    b = bd.Pos((PCB_X0 + PCB_X1) / 2, (PCB_Y0 + PCB_Y1) / 2, FLOOR + z + 0.8) * bd.Box(PCB_X1 - PCB_X0, PCB_Y1 - PCB_Y0, 1.6)
    return named(b, label, rgb)


body = named(make_body(), "case_body", (0.91, 0.81, 0.66))
holder = named(bd.Pos(0, 0, FLOOR) * make_holder(), "holder", (0.36, 0.61, 0.84))
# 頂蓋倒過來印;組裝時繞 X 軸翻 180°,頂板內面貼殼身上緣,再抬開 LIFT
lid = make_lid("A", LID_GAP_VARIANTS["A"])
lid = named(bd.Pos(0, 0, BODY_H + LID_T + LIFT) * bd.Rot(180, 0, 0) * lid, "lid_A_lifted_30mm", (0.79, 0.64, 0.44))
# 示意喇叭:外框、磁鐵、頸部是使用者實測(77.4 方形、總厚 25、磁鐵 Ø40.3 × 6、頸部 Ø36),盆架形狀是示意
from aiy_case import MAG_D, MAG_T, NECK_D, SPK_CX, SPK_CZ, SPK_DEPTH, SPK_SIZE  # noqa: E402
neck_at = SPK_DEPTH - MAG_T                       # 磁鐵前緣離前框表面
speaker = bd.Pos(SPK_CX, IN_Y / 2, SPK_CZ) * bd.Rot(90, 0, 0) * (
    bd.Pos(0, 0, 0.6) * bd.Box(SPK_SIZE, SPK_SIZE, 1.2)
    + bd.Pos(0, 0, 1.2) * bd.Cone(36, NECK_D / 2, neck_at - 3.2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    + bd.Pos(0, 0, neck_at - 2.0) * bd.Cylinder(NECK_D / 2, 2.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    + bd.Pos(0, 0, neck_at) * bd.Cylinder(MAG_D / 2, MAG_T, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)))
speaker = named(speaker, "speaker_dummy", (0.55, 0.55, 0.55))
# 示意按鈕:使用者實測(2026-11-13)頂蓋內面往下伸 24.0、螺紋以下最寬 23.8;跟著頂蓋抬開 LIFT。螺帽(厚 10.4)沒量外徑,不畫
from aiy_case import BTN_FROM_D, y_from_bd  # noqa: E402
BTN_DEPTH, BTN_W = 24.0, 23.8
button = bd.Pos(0, y_from_bd(BTN_FROM_D), BODY_H + LIFT - BTN_DEPTH / 2) * bd.Cylinder(BTN_W / 2, BTN_DEPTH)
button = named(button, "button_dummy_lifted_30mm", (0.85, 0.2, 0.2))

pi = board(PI_Z, "pi_zero_w_dummy", (0.18, 0.49, 0.2))
bonnet = board(BONNET_Z, "voice_bonnet_dummy", (0.4, 0.73, 0.42))
out = HERE / "build"
out.mkdir(exist_ok=True)

# 組裝:頂蓋抬開 LIFT,其他在裝好的位置
asm = bd.Compound(label="AIY_Voice_Kit_case_assembly", children=[body, holder, lid, button, speaker, pi, bonnet])
bd.export_step(asm, str(out / "assembly.step"))
print("寫入", out / "assembly.step")

# 爆炸圖:沿裝配方向拉開。支架連同喇叭、電路板從殼身往上拿出來;喇叭再往 D 面拉、電路板再往 A 面抽出切縫;頂蓋在最上面
UP, SPK_OUT, PCB_OUT, LID_UP = 95.0, 35.0, 55.0, 190.0


def moved(shape, label, loc):
    m = loc * shape
    m.label, m.color = label, shape.color
    return m


exploded = bd.Compound(label="AIY_Voice_Kit_case_exploded", children=[
    moved(body, "case_body", bd.Pos(0, 0, 0)),
    moved(holder, "holder", bd.Pos(0, 0, UP)),
    moved(speaker, "speaker_dummy", bd.Pos(0, SPK_OUT, UP)),
    moved(pi, "pi_zero_w_dummy", bd.Pos(0, -PCB_OUT, UP)),
    moved(bonnet, "voice_bonnet_dummy", bd.Pos(0, -PCB_OUT, UP + 8)),
    moved(lid, "lid_A", bd.Pos(0, 0, LID_UP - LIFT)),
    moved(button, "button_dummy", bd.Pos(0, 0, LID_UP - LIFT)),
])
bd.export_step(exploded, str(out / "assembly_exploded.step"))
print("寫入", out / "assembly_exploded.step")
