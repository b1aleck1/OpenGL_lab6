#!/usr/bin/env python3
import sys
from PIL import Image

from glfw.GLFW import *
from OpenGL.GL import *
from OpenGL.GLU import *

viewer = [0.0, 0.0, 10.0]
theta = 0.0
phi = 0.0
pix2angle = 1.0

left_mouse_button_pressed = 0
mouse_x_pos_old = 0
mouse_y_pos_old = 0
delta_x = 0
delta_y = 0

show_front_wall = True

# Lista na tekstury i indeks aktualnej
texture_ids = []
current_texture_index = 0


def load_texture(filename):
    try:
        image = Image.open(filename)
    except IOError:
        print(f"Błąd: Nie można otworzyć pliku {filename}")
        sys.exit()

    img_data = image.convert("RGB").tobytes("raw", "RGB", 0, -1)

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexImage2D(GL_TEXTURE_2D, 0, 3, image.width, image.height, 0,
                 GL_RGB, GL_UNSIGNED_BYTE, img_data)

    return texture_id


def startup():
    update_viewport(None, 400, 400)
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_CULL_FACE)

    # Wczytujemy kilka tekstur do listy
    global texture_ids
    texture_ids.append(load_texture("tekstury/D1_t.tga"))
    texture_ids.append(load_texture("tekstury/D2_t.tga"))
    texture_ids.append(load_texture("tekstury/D3_t.tga"))
    texture_ids.append(load_texture("tekstury/D4_t.tga"))
    texture_ids.append(load_texture("tekstury/D5_t.tga"))
    texture_ids.append(load_texture("tekstury/M1_t.tga"))
    texture_ids.append(load_texture("tekstury/N1_t.tga"))
    texture_ids.append(load_texture("tekstury/P1_t.tga"))
    # do wyboru, do koloru

    # Ustawiamy pierwszą jako aktywną
    glBindTexture(GL_TEXTURE_2D, texture_ids[0])
    print("Załadowano tekstury. Naciśnij [T] aby przełączać.")


def shutdown():
    pass


def render(time):
    global theta, phi, show_front_wall

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    gluLookAt(viewer[0], viewer[1], viewer[2],
              0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

    if left_mouse_button_pressed:
        theta += delta_x * pix2angle
        phi += delta_y * pix2angle

    glRotatef(theta, 0.0, 1.0, 0.0)
    glRotatef(phi, 1.0, 0.0, 0.0)


    # Podstawa
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0);
    glVertex3f(-5.0, -5.0, 0.0)
    glTexCoord2f(1.0, 0.0);
    glVertex3f(5.0, -5.0, 0.0)
    glTexCoord2f(1.0, 1.0);
    glVertex3f(5.0, 5.0, 0.0)
    glTexCoord2f(0.0, 1.0);
    glVertex3f(-5.0, 5.0, 0.0)
    glEnd()

    # Ściany boczne
    glBegin(GL_TRIANGLES)

    if show_front_wall:
        glTexCoord2f(0.0, 0.0);
        glVertex3f(-5.0, -5.0, 0.0)
        glTexCoord2f(1.0, 0.0);
        glVertex3f(5.0, -5.0, 0.0)
        glTexCoord2f(0.5, 0.5);
        glVertex3f(0.0, 0.0, 5.0)

    glTexCoord2f(1.0, 0.0);
    glVertex3f(5.0, -5.0, 0.0)
    glTexCoord2f(1.0, 1.0);
    glVertex3f(5.0, 5.0, 0.0)
    glTexCoord2f(0.5, 0.5);
    glVertex3f(0.0, 0.0, 5.0)

    glTexCoord2f(1.0, 1.0);
    glVertex3f(5.0, 5.0, 0.0)
    glTexCoord2f(0.0, 1.0);
    glVertex3f(-5.0, 5.0, 0.0)
    glTexCoord2f(0.5, 0.5);
    glVertex3f(0.0, 0.0, 5.0)

    glTexCoord2f(0.0, 1.0);
    glVertex3f(-5.0, 5.0, 0.0)
    glTexCoord2f(0.0, 0.0);
    glVertex3f(-5.0, -5.0, 0.0)
    glTexCoord2f(0.5, 0.5);
    glVertex3f(0.0, 0.0, 5.0)

    glEnd()
    glFlush()


def update_viewport(window, width, height):
    global pix2angle
    pix2angle = 360.0 / width
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(70, 1.0, 0.1, 300.0)
    if width <= height:
        glViewport(0, int((height - width) / 2), width, width)
    else:
        glViewport(int((width - height) / 2), 0, height, height)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def keyboard_key_callback(window, key, scancode, action, mods):
    global show_front_wall, current_texture_index, texture_ids

    if action == GLFW_PRESS:
        if key == GLFW_KEY_ESCAPE:
            glfwSetWindowShouldClose(window, GLFW_TRUE)

        if key == GLFW_KEY_H:
            show_front_wall = not show_front_wall

        # Przełączanie tekstur klawiszem T
        if key == GLFW_KEY_T:
            # Zwiększamy indeks o 1, a modulo (%) sprawia, że jak dojdziemy do końca listy, to wrócimy do 0.
            current_texture_index = (current_texture_index + 1) % len(texture_ids)

            # Podmieniamy aktywną teksturę
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
    window = glfwCreateWindow(400, 400, "Lab 6 - Zadanie 4.5 (Przelaczanie)", None, None)
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