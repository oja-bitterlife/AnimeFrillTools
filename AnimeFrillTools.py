import bpy, mathutils

# 定数
AFT_EMPTY_NAME = "AFT_Empty"
AFT_EMPTY_HOOK_NAME = "AFT_Hook"
AFT_EMPTY_ARMATURE_NAME = "AFT_Armature"


# 作成ボタン
# *************************************************************************************************
# 選択ポイントにコントロール用Emptyを作成する
class AHT_FRILL_OT_create_control_empty(bpy.types.Operator):
    bl_idname = "aht_frill.create_control_empty"
    bl_label = "Create"

    # execute
    def execute(self, context):
        # 先に一旦削除
        for obj in context.selected_objects:
            if obj and obj.type == 'CURVE':
                AHT_FRILL_OT_remove_control_empty.remove(context, obj)
        # create
        for obj in context.selected_objects:
            if obj and obj.type == 'CURVE':
                AHT_FRILL_OT_create_control_empty.create(context, obj)

        return{'FINISHED'}


    @classmethod
    def create(cls, context, curve):
        spline = curve.data.splines[0]
        curve_mat_world = curve.matrix_world

        # ポイントごとにEmpty生成
        PointEmptys = []
        for no, point in enumerate(spline.points):
            empty = bpy.data.objects.new(AFT_EMPTY_NAME, None)
            curve.users_collection[0].objects.link(empty)

            # 初期設定
            empty.parent = curve
            empty.empty_display_size = 0.05
            empty.location = (curve_mat_world @ point.co).xyz
            empty.rotation_euler[2] = point.tilt  # とりあえずZを使う
            empty.show_in_front = True

            # リセット用
            empty["AFT_target_curve"] = curve
            empty["AFT_point_no"] = no
            empty["AFT_org_pos"] = list(empty.location)
            empty["AFT_org_tilt"] = point.tilt

            # この後の設定用にリスト保存
            PointEmptys.append(empty)

        # Hookの追加
        for no, point in enumerate(spline.points):
            hook = curve.modifiers.new("AFT_Hook", 'HOOK')
            hook.object = PointEmptys[no]
            hook.vertex_indices_set([no])
            hook.matrix_inverse = mathutils.Matrix.Translation(-point.co.xyz)

        # Tiltにドライバを設定
        for no, point in enumerate(spline.points):
            driver = point.driver_add('tilt')
            driver.driver.type = 'SCRIPTED'
            var = driver.driver.variables.new()
            var.name = 'var'
            var.type = 'TRANSFORMS'
            var.targets[0].id = PointEmptys[no]
            var.targets[0].transform_type = 'ROT_Z'
            driver.driver.expression = 'var'


# 削除ボタン
# *************************************************************************************************
# 選択ポイントに結びついたEmptyを削除する
class AHT_FRILL_OT_remove_control_empty(bpy.types.Operator):
    bl_idname = "aht_frill.remove_control_empty"
    bl_label = "Remove"

    # execute
    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'CURVE':
                AHT_FRILL_OT_remove_control_empty.remove(context, obj)
        return{'FINISHED'}

    @classmethod
    def remove(cls, context, curve):
        for obj in context.view_layer.objects:
            # Emptyに対してのみ処理が行える
            if obj == None or obj.type != 'EMPTY':
                continue

            # 対象のCurveかチェック
            target_curve = obj.get("AFT_target_curve")
            if target_curve == None or target_curve != curve:
                continue

            # 削除対象
            bpy.data.objects.remove(obj, do_unlink=True)

        # hookも削除
        for mod in curve.modifiers:
            if mod.name.startswith(AFT_EMPTY_HOOK_NAME):
                curve.modifiers.remove(mod)

        # driverも削除
        spline = curve.data.splines[0]
        for no, point in enumerate(spline.points):
            point.driver_remove('tilt')


# リセットボタン
# *************************************************************************************************
# Emptyをプロパティを元にリセットする
class AHT_FRILL_OT_reset_control_empty(bpy.types.Operator):
    bl_idname = "aht_frill.reset_control_empty"
    bl_label = "Reset"

    # execute
    def execute(self, context):
        # アクティブだけじゃなくて選択中のEmpty全部対象にしちゃう
        for obj in context.selected_objects:
            if obj == None or obj.type != 'EMPTY':
                continue

            # AFT用のEmptyかチェック
            target_curve = obj.get("AFT_target_curve")
            if target_curve == None:
                continue

            # 対象ポイント番号は必ずあるはずだけど、ないと操作しようがないので(フェイルセーフ)
            point_no = obj.get("AFT_point_no")
            if point_no == None:
                continue

            # リセット対象だったのでリセット
            org_pos = obj.get("AFT_org_pos")
            if org_pos:
                obj.location.x = org_pos[0]
                obj.location.y = org_pos[1]
                obj.location.z = org_pos[2]

            org_tilt = obj.get("AFT_org_tilt")
            if org_tilt:
                obj.rotation_euler[2] = org_tilt
 
        return{'FINISHED'}


# アーマチュア設定ボタン
# *************************************************************************************************
# EmptyにArmatureを設定する
class AHT_FRILL_OT_create_empty_armature(bpy.types.Operator):
    bl_idname = "aht_frill.create_empty_armature"
    bl_label = "Append"

    # execute
    def execute(self, context):
        bpy.context.edit_object.update_from_editmode()  # 複数オブジェクト選択時は、更新しておかないとselectが上手く取得できない

        # メッシュが選択されていた
        selected = None
        for v in context.view_layer.objects.active.data.vertices:
            if v.select:
                if selected != None:
                    self.report({'ERROR'}, "転送元頂点は1つだけ選択してください")
                    return{'FINISHED'}
                selected = v

        if selected == None:
            self.report({'ERROR'}, "転送元頂点を1つ選択してください")
            return{'FINISHED'}

        # 一旦削除
        AHT_FRILL_OT_remove_empty_armature.remove(context)
        # 追加
        AHT_FRILL_OT_create_empty_armature.create(context, list(selected.groups))

        return{'FINISHED'}

    @classmethod
    def create(cls, context, vertex_groups):
        mesh = context.view_layer.objects.active

        # アクティブだけじゃなくて選択中のEmpty全部対象にしちゃう
        for obj in context.selected_objects:
            if obj == None or obj.type != 'EMPTY':
                continue

            # AFT用のEmptyかチェック
            target_curve = obj.get("AFT_target_curve")
            if target_curve == None:
                continue

            # Armature追加
            # -----------------------------------------------------------------
            constraint = obj.constraints.new(type='ARMATURE')
            constraint.name = AFT_EMPTY_ARMATURE_NAME

            # 頂点グループ全部登録
            for vg in vertex_groups:
                weight = vg.weight
                bone_name = mesh.vertex_groups[vg.group].name
                armature, bone = find_bones_armature(mesh, bone_name)

                # コントロールボーンだった
                if armature == None or bone == None:
                    continue  # 登録しない(デフォームボーンのみ)

                # 頂点グループごとにボーンを設定
                target = constraint.targets.new()
                target.target = context.scene.objects.get(armature.name)
                target.subtarget = bone.name
                target.weight = weight
                

def find_bones_armature(mesh, bone_name):
    for modifier in mesh.modifiers:
        if modifier.type == 'ARMATURE' and modifier.object:
            armature = modifier.object.data

            for bone in armature.bones:
                if bone.use_deform and bone.name in bone_name:
                    return (armature, bone)
    return (None, None)

# EmptyからArmatureを削除する
class AHT_FRILL_OT_remove_empty_armature(bpy.types.Operator):
    bl_idname = "aht_frill.remove_empty_armature"
    bl_label = "Remove"

    # execute
    def execute(self, context):
        AHT_FRILL_OT_remove_empty_armature.remove(context)
        return{'FINISHED'}

    @classmethod
    def remove(cls, context):
        # アクティブだけじゃなくて選択中のEmpty全部対象にしちゃう
        for obj in context.selected_objects:
            if obj == None or obj.type != 'EMPTY':
                continue

            # AFT用のEmptyかチェック
            target_curve = obj.get("AFT_target_curve")
            if target_curve == None:
                continue

            # Armatureの削除
            for constraint in obj.constraints:
                if constraint.name.startswith(AFT_EMPTY_ARMATURE_NAME):
                    obj.constraints.remove(constraint)


# ArmatureのEnable/Disable
# *************************************************************************************************
class AHT_FRILL_OT_enable_empty_armature(bpy.types.Operator):
    bl_idname = "aht_frill.enable_empty_armature"
    bl_label = "Enable"

    # execute
    def execute(self, context):
        # アクティブだけじゃなくて選択中のEmpty全部対象にしちゃう
        for obj in context.selected_objects:
            if obj == None or obj.type != 'EMPTY':
                continue

            # AFT用のEmptyかチェック
            target_curve = obj.get("AFT_target_curve")
            if target_curve == None:
                continue

            for constraint in obj.constraints:
                if constraint.name.startswith(AFT_EMPTY_ARMATURE_NAME):
                    constraint.enabled = True

        return{'FINISHED'}


class AHT_FRILL_OT_disable_empty_armature(bpy.types.Operator):
    bl_idname = "aht_frill.disable_empty_armature"
    bl_label = "Disable"

    # execute
    def execute(self, context):
        # アクティブだけじゃなくて選択中のEmpty全部対象にしちゃう
        for obj in context.selected_objects:
            if obj == None or obj.type != 'EMPTY':
                continue

            # AFT用のEmptyかチェック
            target_curve = obj.get("AFT_target_curve")
            if target_curve == None:
                continue

            for constraint in obj.constraints:
                if constraint.name.startswith(AFT_EMPTY_ARMATURE_NAME):
                    constraint.enabled = False

        return{'FINISHED'}


# Main UI
# ===========================================================================================
# 3DView Tools Panel
class AHT_FRILL_PT_ui(bpy.types.Panel):
    bl_idname = "APT_FRILL_PT_UI"
    bl_label = "Anime Frill Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AHT"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        # Curveは1本のみ対応
        if context.view_layer.objects.active.type == "CURVE":
            curve = context.view_layer.objects.active
            if len(curve.data.splines) != 1:
                layout.label(text="カーブが1本ではありません")
                return

        # ボタン表示
        # ---------------------------------------------------------------------
        # リセットボタンが押せるかチェック
        layout.label(text="Reset Empty's transfrom")
        row = layout.row()
        if context.view_layer.objects.active.type != "EMPTY":  # リセットボタンはEmpty選択時のみ
            row.enabled = False
        row.operator("aht_frill.reset_control_empty")

        # ArmatureのON/OFF
        layout.label(text="Enable/Disable Empty's Armature")
        box = layout.box()
        if context.view_layer.objects.active.type != "EMPTY":  # リセットボタンはEmpty選択時のみ
            box.enabled = False
        row = box.row()
        row.operator("aht_frill.enable_empty_armature")
        row.operator("aht_frill.disable_empty_armature")


        # 作成と削除ボタンが押せるかチェック
        layout.label(text="Create/Remove Empty from Curve")
        box = layout.box()
        if context.view_layer.objects.active.type != "CURVE" or context.mode != "OBJECT":  # Create/RemoveはCurve選択時のみ
            box.enabled = False
        row = box.row()
        row.operator("aht_frill.create_control_empty")
        row.operator("aht_frill.remove_control_empty")

        # ウエイト設定ボタンが押せるかチェック
        layout.label(text="Empty's weight copy from mesh vertex")
        box = layout.box().row()
        row = box.row()
        if context.view_layer.objects.active.type != "MESH" or context.mode != "EDIT_MESH":  # 設定ボタンはMesh選択時のみ
            row.enabled = False
        row.operator("aht_frill.create_empty_armature")

        row = box.row()
        if context.view_layer.objects.active.type != "EMPTY":  # リセットボタンはEmpty選択時のみ
            row.enabled = False
        row.operator("aht_frill.remove_empty_armature")


# 設定用データ
# =================================================================================================
def register():
    pass
