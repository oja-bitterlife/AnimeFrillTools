import bpy

# 定数

# 作成ボタン
# *************************************************************************************************
# 選択ポイントにコントロール用Emptyを作成する
class AHT_FRILL_OT_create_control_empty(bpy.types.Operator):
    bl_idname = "aht_frill.create_control_empty"
    bl_label = "Create Control Empty"

    # execute
    def execute(self, context):
        curve = context.view_layer.objects.active
        spline = curve.data.splines[0]

        # 先に一旦削除
        AHT_FRILL_OT_remove_control_empty.remove(context, curve)

        # ポイントごとにEmpty生成
        for point in spline.points:
            obj = bpy.data.objects.new("AFT_Empty", None)
            bpy.data.collections[context.scene.frill_empty_collection].objects.link(obj)

            obj.empty_display_size = 0.05
            obj.location = point.co.xyz

            # リセット用
            obj["AFT_target_curve"] = curve
            obj["AFT_org_pos"] = list(point.co.xyz)
            obj["AFT_org_tilt"] = point.tilt

        return{'FINISHED'}


# 削除ボタン
# *************************************************************************************************
# 選択ポイントに結びついたEmptyを削除する
class AHT_FRILL_OT_remove_control_empty(bpy.types.Operator):
    bl_idname = "aht_frill.remove_control_empty"
    bl_label = "Remove Control Empty"

    # execute
    def execute(self, context):
        curve = context.view_layer.objects.active
        AHT_FRILL_OT_remove_control_empty.remove(context, curve)
        return{'FINISHED'}

    @classmethod
    def remove(cls, context, curve):
        for obj in context.view_layer.objects:
            if obj.type != 'EMPTY':
                continue

            target_curve = obj.get("AFT_target_curve")
            if target_curve == None or target_curve != curve:
                continue

            # 削除対象
            bpy.data.objects.remove(obj, do_unlink=True)


# リセットボタン
# *************************************************************************************************
# 選択ポイントに結びついたEmptyを削除する
class AHT_FRILL_OT_remove_control_empty(bpy.types.Operator):
    bl_idname = "aht_frill.remove_control_empty"
    bl_label = "Remove Control Empty"

    # execute
    def execute(self, context):
        curve = context.view_layer.objects.active
        AHT_FRILL_OT_remove_control_empty.remove(context, curve)
        return{'FINISHED'}

    @classmethod
    def remove(cls, context, curve):
        for obj in context.view_layer.objects:
            if obj.type != 'EMPTY':
                continue

            target_curve = obj.get("AFT_target_curve")
            if target_curve == None or target_curve != curve:
                continue

            # 削除対象
            bpy.data.objects.remove(obj, do_unlink=True)



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

        if context.view_layer.objects.active == None or context.view_layer.objects.active.type != "CURVE":
            layout.label(text="カーブを選択してください")
            return
        curve = context.view_layer.objects.active

        if len(curve.data.splines) != 1:
            layout.label(text="カーブが1本ではありません")
            return
        spline = curve.data.splines[0]

        # オブジェクトモード用
        if context.mode != "OBJECT" and context.mode != "EDIT_CURVE":
            layout.enabled = False

        box = layout.box()
        row = box.row()
        row.label(text="empty's place")
        row.prop(context.scene, "frill_empty_collection", text="")
        box.operator("aht_frill.create_control_empty")
        box.operator("aht_frill.remove_control_empty")


# セレクトボックスに表示したい項目リストを作成する関数
def get_collection_list(scene, context):
    # list[(id, text, desc)]
    items = [(collection.name, collection.name, "") for collection in bpy.data.collections]
    items = [("", "Choose Collection", "")] + items
    return items

# 設定用データ
# =================================================================================================
def register():
    bpy.types.Scene.frill_empty_collection = bpy.props.EnumProperty(name = "Collection Name", description = "Collection Name", items = get_collection_list)
