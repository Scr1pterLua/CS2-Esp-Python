import pymem, pymem.process
import pymem.thread
import win32gui
import win32con
import imgui
from imgui.integrations.glfw import GlfwRenderer
import glfw
import OpenGL.GL as gl
from requests import get
ScreenY = 1920
ScreenX = 1080
offsets = get('https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json').json()
client_dll = get('https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client.dll.json').json()
dwEntityList = offsets["client.dll"]["dwEntityList"]
print("[+] [dwEntityList]")
dwLocalPlayerPawn = offsets["client.dll"]["dwLocalPlayerPawn"]
print("[+] [dwLocalPlayerPawn]")
dwViewMatrix = offsets["client.dll"]["dwViewMatrix"]
print("[+] [dwViewMatrix]")
m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
print("[+] [m_iTeamNum]")
m_lifeState = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_lifeState']
print("[+] [m_lifeState]")
m_pGameSceneNode = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_pGameSceneNode']
print("[+] [m_pGameSceneNode]")
m_modelState = client_dll['client.dll']['classes']['CSkeletonInstance']['fields']['m_modelState']
print("[+] [m_modelState]")
m_hPlayerPawn = client_dll['client.dll']['classes']['CCSPlayerController']['fields']['m_hPlayerPawn']
print("[+] [m_hPlayerPawn]")
m_iIDEntIndex = client_dll["client.dll"]["classes"]["C_CSPlayerPawnBase"]["fields"]["m_iIDEntIndex"]
print("[+] [m_iIDEntIndex]")
pm = pymem.Pymem("cs2.exe")
client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll


def w2s(mtx, posx, posy, posz, width, height):
    screenW = (mtx[12] * posx) + (mtx[13] * posy) + (mtx[14] * posz) + mtx[15]

    if screenW > 0.001:
        screenX = (mtx[0] * posx) + (mtx[1] * posy) + (mtx[2] * posz) + mtx[3]
        screenY = (mtx[4] * posx) + (mtx[5] * posy) + (mtx[6] * posz) + mtx[7]

        camX = width / 2
        camY = height / 2

        x = camX + (camX * screenX / screenW)//1
        y = camY - (camY * screenY / screenW)//1

        return [x, y]

    return [-999, -999]

# ESP function
def esp(draw_list):
    view_matrix = []
    
    for i in range(64):
       
        temp_mat_val = pm.read_float(client + dwViewMatrix + i * 4)
        view_matrix.append(temp_mat_val)

    local_player_pawn_addr = pm.read_longlong(client + dwLocalPlayerPawn)

    try:
        local_player_team = pm.read_int(local_player_pawn_addr + m_iTeamNum)
    except:
        print("You are not in game")
        return

    for i in range(64):
        
        entity = pm.read_longlong(client + dwEntityList)

        if not entity:
            continue

        list_entry = pm.read_longlong(entity + ((8 * (i & 0x7FFF) >> 9) + 16))

        if not list_entry:
            continue

        entity_controller = pm.read_longlong(list_entry + (120) * (i & 0x1FF))

        if not entity_controller:
            continue

        entity_controller_pawn = pm.read_longlong(entity_controller + m_hPlayerPawn)

        if not entity_controller_pawn:
            continue

        list_entry = pm.read_longlong(entity + (0x8 * ((entity_controller_pawn & 0x7FFF) >> 9) + 16))

        if not list_entry:
            continue

        entity_pawn_addr = pm.read_longlong(list_entry + (120) * (entity_controller_pawn & 0x1FF))

        if not entity_pawn_addr or entity_pawn_addr == local_player_pawn_addr:
            continue

        entity_alive = pm.read_int(entity_pawn_addr + m_lifeState)

        if entity_alive != 256:
            continue
        entity_team = pm.read_int(entity_pawn_addr + m_iTeamNum)
        if entity_team == local_player_team:
              continue
        
        
        
       
        

    
    
        
        color = imgui.get_color_u32_rgba(0, 0.7, 1, 1)
        
           
       
      
            

        game_scene = pm.read_longlong(entity_pawn_addr + m_pGameSceneNode)
        bone_matrix = pm.read_longlong(game_scene + m_modelState + 0x80)

        try:
            
                headX = pm.read_float(bone_matrix + 6 * 0x20)
                headY = pm.read_float(bone_matrix + 6 * 0x20 + 0x4)
                headZ = pm.read_float(bone_matrix + 6 * 0x20 + 0x8) + 8

                head_pos = w2s(view_matrix, headX, headY, headZ, ScreenY, ScreenX)

            
                center_x = ScreenY / 2
                center_y = ScreenX / 2

                draw_list.add_line(center_x, center_y, head_pos[0], head_pos[1], color, 0.1)

                legZ = pm.read_float(bone_matrix + 28 * 0x20 + 0x8)

                leg_pos = w2s(view_matrix, headX, headY, legZ, ScreenY,ScreenX)

                deltaZ = abs(head_pos[1] - leg_pos[1])

                leftX = head_pos[0] - deltaZ // 3.5
                rightX = head_pos[0] + deltaZ // 3.5

                draw_list.add_line(leftX, head_pos[1], rightX, head_pos[1], color, 1)
                draw_list.add_line(leftX, leg_pos[1], rightX, leg_pos[1], color, 1)

                draw_list.add_line(leftX, head_pos[1], leftX, leg_pos[1], color, 1)
                draw_list.add_line(rightX, head_pos[1], rightX, leg_pos[1], color, 1)
            

        except:
            print("cant get bones")
            return


def main():
    if not glfw.init():
        print("Could not initialize OpenGL context")
        exit(1)
    glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
    window = glfw.create_window(ScreenY, ScreenX, "Overlay", None, None)

    hwnd = glfw.get_win32_window(window)

    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    style &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME)
    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

    ex_style = win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, -2, -2, 0, 0,
                          win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

    glfw.make_context_current(window)

    imgui.create_context()
    impl = GlfwRenderer(window)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        imgui.new_frame()
        imgui.set_next_window_size(ScreenY, ScreenX)
        imgui.set_next_window_position(0, 0)

        imgui.begin("overlay", flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_BACKGROUND)
        draw_list = imgui.get_window_draw_list()

        esp(draw_list)

        imgui.end()
        imgui.end_frame()

        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()

if __name__ == '__main__':
    main()
