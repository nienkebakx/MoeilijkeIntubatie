# -*- coding: utf-8 -*-
"""
Created on Fri Jul  2 15:10:34 2021

@author: nienkebakx
"""

from tkinter import *
from tkinter import filedialog
import os
from PIL import ImageTk, Image, ImageOps
import face_alignment
from skimage import io, segmentation, transform
import numpy as np
import math


class MyWindow:
    def __init__(self, parent):
        self.parent = parent
        self.frame_image = LabelFrame(self.parent)
        self.frame_image.grid(row=0, column=0, rowspan = 3)
        self.frame_buttons = LabelFrame(self.parent)
        self.frame_buttons.grid(row=0, column=1)
        
        self.load_button = Button(self.frame_buttons, text = 'Selecteer foto', command = self.load)
        self.load_button.grid(row=1, column=1, pady = 1)
        
        self.reference_size = 5
        self.reference_size_label = Label(self.frame_buttons, text= "Grootte referentie object (cm):")
        self.reference_size_label.grid(row=2, column=1, padx=5, pady=1)
        self.reference_size_entry = Entry(self.frame_buttons, width=5)        
        self.reference_size_entry.grid(row=2, column=2, padx=5, pady=1)
        self.reference_size_entry.insert(0, self.reference_size)
        
        self.distance_camera = 100
        self.distance_camera_label = Label(self.frame_buttons, text= "Afstand tot camera (cm):")
        self.distance_camera_label.grid(row=3, column=1)
        self.distance_camera_entry = Entry(self.frame_buttons, width=8)        
        self.distance_camera_entry.grid(row=3, column=2)
        self.distance_camera_entry.insert(0, self.distance_camera)
        
        self.factor_long = Label(self.frame_buttons, text = "Factor lange zijde:")
        self.factor_long.grid(row=6, column=1)
        self.factor_long_entry = Entry(self.frame_buttons, width=8)
        self.factor_long_entry.grid(row=6, column=2)
        self.factor_long_entry.configure(state='disabled')
        
        self.factor_short = Label(self.frame_buttons, text = "Factor korte zijde:")
        self.factor_short.grid(row=7, column=1)
        self.factor_short_entry = Entry(self.frame_buttons, width=8)
        self.factor_short_entry.grid(row=7, column=2)
        self.factor_short_entry.configure(state='disabled')
                
        self.canvas = Canvas(self.frame_image, height = 750, width = 650)
        self.image = self.canvas.create_image((400, 400), image=ImageTk.PhotoImage(image=Image.fromarray(np.zeros(400))))
        self.canvas.grid()
        
        self.ref1 = None
        self.ref2 = None
        self.ref3 = None
        self.ref4 = None
        self.x_ref = None
        self.y_ref = None
        self.ref_mask = None
        self.image_coords_initial = None 
        self.ref_coords_button = Button(self.frame_buttons, text='Selecteer referentie object', command=self.visualize_referentie)
        self.ref_coords_button.grid(row=4, column=1, padx=5, pady=1)
        self.ref_reset_button_ref = Button(self.frame_buttons, text='Reset referentie object', command=self.reset_referentie)
        self.ref_reset_button_ref.grid(row=4, column=2, padx=5, pady=1)

        self.calculate_facts_button = Button(self.frame_buttons, text='Bereken factoren', command=self.calculate_factors)
        self.calculate_facts_button.grid(row=5, column=1, padx=5, pady=1)
        self.reset_facts_button = Button(self.frame_buttons, text='Reset factoren', command=self.reset_factors)
        self.reset_facts_button.grid(row=5, column=2, padx=5, pady=1)

        self.canvas.tag_bind("token", "<ButtonPress-1>", self.drag_start)
        self.canvas.tag_bind("token", "<ButtonRelease-1>", self.drag_stop)
        self.canvas.tag_bind("token", "<B1-Motion>", self.drag)
        self.drag_data = {"x": 0, "y": 0, "item": None}
   

        
    def load(self):
        self.status = Label(self.parent, text="Status = OK", bd=1, relief=SUNKEN, anchor=W)
        self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
         
        self.filename = filedialog.askopenfilename(initialdir = os.getcwd(), title = 'Selecteer foto', filetypes=[('image files', ('.png','.jpg','.jpeg'))])
        if not self.filename:
            self.status = Label(self.parent, text="Geen afbeelding ingeladen", bd=1, relief=SUNKEN, anchor=W, fg='red')
            self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)


        self.canvas.delete('all')        
        self.orig_image = Image.open(self.filename)               
        self.orig_image = ImageOps.exif_transpose(self.orig_image)
        self.img_width = float(self.orig_image.size[0])
        self.img_height = float(self.orig_image.size[1])
        self.orig_image = ImageTk.PhotoImage(self.orig_image)
        self.canvas_image = self.canvas.create_image(self.img_width/2, self.img_height/2, image=self.orig_image, tags = ("token"))
        self.canvas.grid()
            
        self.image = io.imread(self.filename)
        self.image_coords_initial = self.canvas.coords("token")


    def get_referentie_object(self):
        self.canvas.bind("<Button 1>", self.get_coords)   
        
    def visualize_referentie(self):
        if self.x_ref is None:
            self.status = Label(self.parent, text="Klik op referentie object en klik opnieuw op knop", bd=1, relief=SUNKEN, anchor=W, fg='red')
            self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
            self.get_referentie_object()
        if not self.x_ref is None:
        
            self.status = Label(self.parent, text="Status = OK", bd=1, relief=SUNKEN, anchor=W)
            self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
            
            image_coords = self.canvas.coords("token")
            y_dif = self.image_coords_initial[0] - image_coords[0]
            x_dif = self.image_coords_initial[1] - image_coords[1]
            
            y_ref = self.x_ref + y_dif
            x_ref = self.y_ref + x_dif
            
            self.mask = segmentation.flood(self.image[:,:,0], (int(x_ref), int(y_ref)),tolerance = 10)
            self.ref_mask = np.argwhere(self.mask)
            self.ref1 = self.canvas.create_oval(min(self.ref_mask[:,1])-2-y_dif, min(self.ref_mask[:,0])-2-x_dif, min(self.ref_mask[:,1])+2-y_dif, min(self.ref_mask[:,0])+2-x_dif, fill = 'blue')
            self.ref2 = self.canvas.create_oval(min(self.ref_mask[:,1])-2-y_dif, max(self.ref_mask[:,0])-2-x_dif, min(self.ref_mask[:,1])+2-y_dif, max(self.ref_mask[:,0])+2-x_dif, fill = 'blue')
            self.ref3 = self.canvas.create_oval(max(self.ref_mask[:,1])-2-y_dif, min(self.ref_mask[:,0])-2-x_dif, max(self.ref_mask[:,1])+2-y_dif, min(self.ref_mask[:,0])+2-x_dif, fill = 'blue')
            self.ref4 = self.canvas.create_oval(max(self.ref_mask[:,1])-2-y_dif, max(self.ref_mask[:,0])-2-x_dif, max(self.ref_mask[:,1])+2-y_dif, max(self.ref_mask[:,0])+2-x_dif, fill = 'blue')


    def reset_referentie(self):
        self.x_ref = None
        
        self.canvas.delete(self.ref1)
        self.canvas.delete(self.ref2)
        self.canvas.delete(self.ref3)
        self.canvas.delete(self.ref4)
        self.ref_mask = None
        
    def calculate_factors(self):
        D_cm = int(self.distance_camera_entry.get())
        h_obj_cm = float(self.reference_size_entry.get())
        v_obj_cm = float(self.reference_size_entry.get())
        
        h_sensor_pix = self.image.shape[1]
        v_sensor_pix = self.image.shape[0]
            
        h_obj_pix = max(self.ref_mask[:,0]) - min(self.ref_mask[:,0])
        v_obj_pix = max(self.ref_mask[:,1]) - min(self.ref_mask[:,1])
            
        h_factor = h_obj_cm/D_cm * h_sensor_pix/h_obj_pix
        v_factor = v_obj_cm/D_cm * v_sensor_pix/v_obj_pix
        
        if self.image.shape[0] > self.image.shape[1]: #portret
            
            self.factor_long_entry.configure(state='normal')
            self.factor_long_entry.insert(0, round(v_factor,2))
            self.factor_long_entry.configure(state='disabled')
            self.factor_short_entry.configure(state='normal')
            self.factor_short_entry.insert(0, round(h_factor,2))
            self.factor_short_entry.configure(state='disabled')
        
        else: #landschap

            self.factor_long_entry.configure(state='normal')
            self.factor_long_entry.insert(0, round(h_factor,2))
            self.factor_long_entry.configure(state='disabled')
            self.factor_short_entry.configure(state='normal')
            self.factor_short_entry.insert(0, round(v_factor,2))
            self.factor_short_entry.configure(state='disabled')            
            
        
    def reset_factors(self):
        self.factor_long_entry.configure(state='normal')
        self.factor_long_entry.delete(0,'end')
        self.factor_long_entry.configure(state='disabled')
        self.factor_short_entry.configure(state='normal')
        self.factor_short_entry.delete(0,'end')
        self.factor_short_entry.configure(state='disabled')
        

    def get_coords(self, event):
        self.x_ref = event.x
        self.y_ref = event.y
        
        
    def drag_start(self, event):
        self.drag_data["item"] = self.canvas_image
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y


    def drag_stop(self, event):
        self.drag_data["item"] = None
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0

            
    def drag(self, event):
        delta_x = event.x - self.drag_data["x"]
        delta_y = event.y - self.drag_data["y"]
        self.canvas.move(self.canvas_image, delta_x, delta_y)
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
         
            

if __name__ == '__main__':
    root = Tk()
    root.title('Configuratie Instellingen')
    top = MyWindow(root)
    root.mainloop()