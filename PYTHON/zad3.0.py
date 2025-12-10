#!/usr/bin/env python3
import sys
from PIL import Image

from glfw.GLFW import *
from OpenGL.GL import *
from OpenGL.GLU import *

viewer = [0.0, 0.0, 10.0]
theta = 0.0
pix2angle = 1.0

left_mouse_button_pressed = 0
mouse_x_pos_old = 0
delta_x = 0


def load_texture(filename):
    try:
        image = Image.open(filename)
    except IOError:
        print(f"Błąd: Nie można otworzyć pliku {filename}")
        sys.exit()

    # Konwersja obrazu na bajty (RGB), TGA często przechowuje dane, które Pillow czyta bez problemu
    img_data = image.convert("RGB").tobytes("raw", "RGB", 0, -1)

    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)

    # Ustawienia filtrowania
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

    load_texture("tekstura.tga")


def shutdown():
    pass


def render(time):
    global theta

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    gluLookAt(viewer[0], viewer[1], viewer[2],
              0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

    if left_mouse_button_pressed:
        theta += delta_x * pix2angle

    glRotatef(theta, 0.0, 1.0, 0.0)

    # Składamy kwadrat z dwóch trójkątów.
    # Kolejność wierzchołków musi być CCW (przeciwnie do zegara), żeby face culling nie usunął przodu

    glBegin(GL_TRIANGLES)

    # Pierwszy trójkąt (dolna lewa połówka)
    # Format: glTexCoord2f(u, v); glVertex3f(x, y, z)
    glTexCoord2f(0.0, 0.0);
    glVertex3f(-5.0, -5.0, 0.0)  # Lewy dolny
    glTexCoord2f(1.0, 0.0);
    glVertex3f(5.0, -5.0, 0.0)  # Prawy dolny
    glTexCoord2f(0.0, 1.0);
    glVertex3f(-5.0, 5.0, 0.0)  # Lewy górny

    # Drugi trójkąt (górna prawa połówka)
    glTexCoord2f(1.0, 0.0);
    glVertex3f(5.0, -5.0, 0.0)  # Prawy dolny
    glTexCoord2f(1.0, 1.0);
    glVertex3f(5.0, 5.0, 0.0)  # Prawy górny
    glTexCoord2f(0.0, 1.0);
    glVertex3f(-5.0, 5.0, 0.0)  # Lewy górny

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
    if key == GLFW_KEY_ESCAPE and action == GLFW_PRESS:
        glfwSetWindowShouldClose(window, GLFW_TRUE)


def mouse_motion_callback(window, x_pos, y_pos):
    global delta_x
    global mouse_x_pos_old

    delta_x = x_pos - mouse_x_pos_old
    mouse_x_pos_old = x_pos


def mouse_button_callback(window, button, action, mods):
    global left_mouse_button_pressed

    if button == GLFW_MOUSE_BUTTON_LEFT and action == GLFW_PRESS:
        left_mouse_button_pressed = 1
    else:
        left_mouse_button_pressed = 0


def main():
    if not glfwInit():
        sys.exit(-1)

    window = glfwCreateWindow(400, 400, "Lab 6 - Zadanie 3.0", None, None)
    if not window:
        glfwTerminate()
        sys.exit(-1)

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