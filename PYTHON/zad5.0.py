#!/usr/bin/env python3
import sys
import math
import numpy as np
from PIL import Image

from glfw.GLFW import *
from OpenGL.GL import *
from OpenGL.GLU import *

# --- KONFIGURACJA ---
N = 50  # Rozdzielczość jajka (im więcej, tym gładsze)
viewer = [0.0, 0.0, 15.0]  # Kamera oddalona na osi Z

# Zmienne do obracania myszką
theta = 0.0
phi = 0.0
pix2angle = 1.0
left_mouse_button_pressed = 0
mouse_x_pos_old = 0
mouse_y_pos_old = 0
delta_x = 0
delta_y = 0

# Tablice na dane jajka
VERTICES = np.zeros((N, N, 3))
UV_COORDS = np.zeros((N, N, 2))  # Tablica na współrzędne tekstury

# Tekstury
texture_ids = []
current_texture_index = 0


def load_texture(filename):
    try:
        image = Image.open(filename)
    except IOError:
        print(f"Błąd: Nie można otworzyć pliku {filename}. Pomijam.")
        return None

    # Często w OpenGL trzeba obrócić obrazek, bo współrzędne (0,0) są w innym rogu
    # Jeśli tekstura jest do góry nogami, odkomentuj linię poniżej:
    # image = image.transpose(Image.FLIP_TOP_BOTTOM)

    img_data = image.convert("RGB").tobytes("raw", "RGB", 0, -1)

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexImage2D(GL_TEXTURE_2D, 0, 3, image.width, image.height, 0,
                 GL_RGB, GL_UNSIGNED_BYTE, img_data)

    return texture_id


def oblicz_punkty_jajka():
    """Wylicza wierzchołki jajka i współrzędne tekstury"""
    u_vals = np.linspace(0.0, 1.0, N)
    v_vals = np.linspace(0.0, 1.0, N)
    pi = math.pi

    for i in range(N):
        for j in range(N):
            u = u_vals[i]
            v = v_vals[j]

            # --- Matematyka jajka ---
            # Wzór parametryczny
            u2 = u * u
            u3 = u2 * u
            u4 = u3 * u
            u5 = u4 * u

            poly_u = (-90 * u5 + 225 * u4 - 270 * u3 + 180 * u2 - 45 * u)

            x = poly_u * math.cos(pi * v)
            z = poly_u * math.sin(pi * v)
            y = 160 * u4 - 320 * u3 + 160 * u2 - 5.0  # -5 wyśrodkowuje jajko w pionie

            VERTICES[i][j] = [x, y, z]

            # --- Współrzędne tekstury ---
            # Mapujemy u i v bezpośrednio na współrzędne tekstury (0.0 do 1.0)
            UV_COORDS[i][j] = [u, v]


def startup():
    update_viewport(None, 400, 400)
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)

    glEnable(GL_CULL_FACE)

    # Czasem trzeba zmienić na GL_BACK, zależnie od sterownika,
    # ale przy tym sposobie rysowania GL_FRONT zazwyczaj działa ok dla jajka.
    glCullFace(GL_FRONT)

    global texture_ids

    pliki_tekstur = [
        "tekstury/P1_t.tga",
        "tekstury/P2_t.tga",
        "tekstury/dirt.tga",
        "tekstury/tekstura.tga",
        "tekstury/moja-tekstura.tga"
    ]

    print("Ładowanie tekstur...")
    for plik in pliki_tekstur:
        tid = load_texture(plik)
        if tid is not None:
            texture_ids.append(tid)

    if texture_ids:
        glBindTexture(GL_TEXTURE_2D, texture_ids[0])
        print(f"Załadowano {len(texture_ids)} tekstur.")
        print("Sterowanie: Myszka (LPM) - obrót. Klawisz [T] - zmiana tekstury.")
    else:
        print("UWAGA: Nie znaleziono tekstur! Jajko będzie czarne.")
        # Dodajemy '0' żeby program nie padł
        texture_ids.append(0)

    oblicz_punkty_jajka()


def shutdown():
    pass


def render(time):
    global theta, phi

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Ustawienie kamery
    gluLookAt(viewer[0], viewer[1], viewer[2],
              0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

    # Obsługa obrotu myszką
    if left_mouse_button_pressed:
        theta += delta_x * pix2angle
        phi += delta_y * pix2angle

    glRotatef(theta, 0.0, 1.0, 0.0)  # Obrót wokół osi Y
    glRotatef(phi, 1.0, 0.0, 0.0)  # Obrót wokół osi X

    # Rysowanie jajka
    glBegin(GL_TRIANGLES)
    for i in range(N - 1):
        for j in range(N - 1):

            # Pobieramy współrzędne wierzchołków i tekstur
            # P1 -- P3
            # |     |
            # P2 -- P4
            # Uwaga: w tablicy jest [i][j], [i+1][j]...

            # Wierzchołki
            p1 = VERTICES[i][j]
            p2 = VERTICES[i + 1][j]
            p3 = VERTICES[i][j + 1]
            p4 = VERTICES[i + 1][j + 1]

            # Tekstury
            t1 = UV_COORDS[i][j]
            t2 = UV_COORDS[i + 1][j]
            t3 = UV_COORDS[i][j + 1]
            t4 = UV_COORDS[i + 1][j + 1]

            # --- RYSOWANIE TRÓJKĄTÓW ---
            # Musimy obsłużyć Face Culling. W połowie jajka (i >= N/2)
            # siatka "zawija się", przez co wektory normalne celują do środka.
            # Żeby tekstura była na zewnątrz, w drugiej połowie odwracamy kolejność rysowania.

            if i < N / 2:
                # POŁOWA 1: Normalna kolejność
                # Trójkąt 1
                glTexCoord2fv(t1);
                glVertex3fv(p1)
                glTexCoord2fv(t2);
                glVertex3fv(p2)
                glTexCoord2fv(t3);
                glVertex3fv(p3)
                # Trójkąt 2
                glTexCoord2fv(t2);
                glVertex3fv(p2)
                glTexCoord2fv(t4);
                glVertex3fv(p4)
                glTexCoord2fv(t3);
                glVertex3fv(p3)
            else:
                # POŁOWA 2: Odwrócona kolejność (zamiana wierzchołków 2 i 3 miejscami)
                # Trójkąt 1
                glTexCoord2fv(t1);
                glVertex3fv(p1)
                glTexCoord2fv(t3);
                glVertex3fv(p3)  # Zamiana
                glTexCoord2fv(t2);
                glVertex3fv(p2)  # Zamiana
                # Trójkąt 2
                glTexCoord2fv(t2);
                glVertex3fv(p2)
                glTexCoord2fv(t3);
                glVertex3fv(p3)  # Zamiana
                glTexCoord2fv(t4);
                glVertex3fv(p4)  # Zamiana

    glEnd()
    glFlush()


def update_viewport(window, width, height):
    global pix2angle
    if width == 0: width = 1
    if height == 0: height = 1
    pix2angle = 360.0 / width

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(70, width / height, 0.1, 300.0)
    glViewport(0, 0, width, height)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def keyboard_key_callback(window, key, scancode, action, mods):
    global current_texture_index
    if action == GLFW_PRESS:
        if key == GLFW_KEY_ESCAPE:
            glfwSetWindowShouldClose(window, GLFW_TRUE)

        # Przełączanie tekstur [T]
        if key == GLFW_KEY_T and texture_ids:
            current_texture_index = (current_texture_index + 1) % len(texture_ids)
            glBindTexture(GL_TEXTURE_2D, texture_ids[current_texture_index])
            print(f"Zmieniono teksturę na indeks: {current_texture_index}")


def mouse_motion_callback(window, x_pos, y_pos):
    global delta_x, mouse_x_pos_old, delta_y, mouse_y_pos_old
    delta_x = x_pos - mouse_x_pos_old
    mouse_x_pos_old = x_pos
    delta_y = y_pos - mouse_y_pos_old
    mouse_y_pos_old = y_pos


def mouse_button_callback(window, button, action, mods):
    global left_mouse_button_pressed
    if button == GLFW_MOUSE_BUTTON_LEFT and action == GLFW_PRESS:
        left_mouse_button_pressed = 1
    else:
        left_mouse_button_pressed = 0


def main():
    if not glfwInit(): sys.exit(-1)
    window = glfwCreateWindow(600, 600, "Lab 5.0 - Jajko Tekstura", None, None)
    if not window: glfwTerminate(); sys.exit(-1)

    glfwMakeContextCurrent(window)
    glfwSetFramebufferSizeCallback(window, update_viewport)
    glfwSetKeyCallback(window, keyboard_key_callback)
    glfwSetCursorPosCallback(window, mouse_motion_callback)
    glfwSetMouseButtonCallback(window, mouse_button_callback)
    glfwSwapInterval(1)

    startup()

    while not glfwWindowShouldClose(window):
        render(glfwGetTime())
        glfwSwapBuffers(window)
        glfwPollEvents()

    shutdown()
    glfwTerminate()


if __name__ == '__main__':
    main()