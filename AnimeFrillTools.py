import bpy
import json

# 定数



# Main UI
# ===========================================================================================
# 3DView Tools Panel
class AOV_MUTE_PT_ui(bpy.types.Panel):
    bl_idname = "APT_FRILL_PT_UI"
    bl_label = "Anime Frill Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AHT"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pass


# 設定用データ
# =================================================================================================
def register():
    pass
