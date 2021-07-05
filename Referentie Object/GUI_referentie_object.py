# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 14:51:50 2021

@author: nienkebakx
"""

from tkinter import *
from tkinter import filedialog
import os
from PIL import ImageTk, Image, ImageOps
import face_alignment
from skimage import io, segmentation, transform
import numpy as np


class MyWindow:
    def __init__(self, parent):
        self.parent = parent
        self.frame_image_mouth = LabelFrame(self.parent, text = 'Vooraanzicht - Mond Open')
        self.frame_image_mouth.grid(row=0, column=0, rowspan = 2)
        self.frame_image_side = LabelFrame(self.parent, text= 'Zijaanzicht')
        self.frame_image_side.grid(row=0, column=1, rowspan = 2)
        self.frame_buttons = LabelFrame(self.parent)
        self.frame_buttons.grid(row=0, column=2)
        self.frame_distances = LabelFrame(self.parent, text="Gemeten Afstanden (cm):")
        self.frame_distances.grid(row=1, column=2)
              
        self.filename = None
        self.image = None
        self.x_ref = None
        self.y_ref = None
        self.ref_mask_mouth = None
        self.ref_mask_side = None
        self.preds_sfd_mouth = None
        self.preds_sfd_side = None
        self.position = StringVar()
        self.position.set('Rechts')
        self.ref1_m = None
        self.ref2_m = None
        self.ref3_m = None
        self.ref4_m = None
        self.ref1_s = None
        self.ref2_s = None
        self.ref3_s = None
        self.ref4_s = None 
        self.line1 = None
        self.line2 = None
        self.line3 = None
        self.image_mouth_coords_initial = None       
        self.image_side_coords_initial = None 
        self.reference_size = 5
        
        self.reference_size_label = Label(self.frame_buttons, text= "Grootte referentie object (cm):")
        self.reference_size_label.grid(row=4, column=1, padx=5, pady=1)
        self.reference_size_entry = Entry(self.frame_buttons, width=5)        
        self.reference_size_entry.grid(row=4, column=2, padx=5, pady=1)
        self.reference_size_entry.insert(0, self.reference_size)
        
        self.load_button = Button(self.frame_buttons, text = 'Selecteer foto', command = self.load)
        self.load_button.grid(row=1, column=1, pady = 1)
        
        self.photo_reset_button = Button(self.frame_buttons, text = 'Reset foto', command = self.reset_photo)
        self.photo_reset_button.grid(row=1, column=2, pady=1)
        
        self.predict_button = Button(self.frame_buttons, text='Voorspel punten', command=self.predict)
        self.predict_button.grid(row=2, column=1, padx=5, pady=1)
        
        self.ref_coords_button = Button(self.frame_buttons, text='Selecteer ref object', command=self.visualize_referentie)
        self.ref_coords_button.grid(row=3, column=1, padx=5, pady=1)
        
        self.ref_reset_button_ref = Button(self.frame_buttons, text='Reset ref object', command=self.reset_referentie)
        self.ref_reset_button_ref.grid(row=3, column=2, padx=5, pady=1)
        
        self.canvas_mouth = Canvas(self.frame_image_mouth, height = 750, width = 650)
        self.image_mouth = self.canvas_mouth.create_image((400, 400), image=ImageTk.PhotoImage(image=Image.fromarray(np.zeros(400))))
        self.canvas_mouth.grid()
  
        self.canvas_side = Canvas(self.frame_image_side, height = 750, width = 650)
        self.image_side = self.canvas_side.create_image((400, 400), image=ImageTk.PhotoImage(image=Image.fromarray(np.zeros(400))))
        self.canvas_side.grid()
        
        self.status = Label(self.parent, text="Status = OK", bd=1, relief=SUNKEN, anchor=W)
        self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
                   
        self.drop_position = OptionMenu(self.frame_buttons, self.position, "Rechts", "Links", "Mond open")
        self.drop_position.grid(row=0, column=1, padx=5, pady=1)
        
        self.distances_button = Button(self.frame_buttons, text='Bereken afstanden', command=self.distances)
        self.distances_button.grid(row=5, column=1, padx=5, pady=1)
        
        self.ref_reset_button_dist = Button(self.frame_buttons, text='Reset afstanden', command=self.reset_distances_all)
        self.ref_reset_button_dist.grid(row=5, column=2, padx=5, pady=1)
        
        self.points_reset_button = Button(self.frame_buttons, text='Reset punten', command=self.reset_points)
        self.points_reset_button.grid(row=2, column=2, padx=5, pady=1)
        
        self.distance_mouth = Label(self.frame_distances, text = "Mond opening:")
        self.distance_mouth.grid(row=0, column=0)
        self.distance_mouth_entry = Entry(self.frame_distances)
        self.distance_mouth_entry.grid(row=0, column=1)
        self.distance_mouth_entry.configure(state='disabled')

        self.distance_jaw = Label(self.frame_distances, text = "Kin - kaak:")
        self.distance_jaw.grid(row=1, column=0)
        self.distance_jaw_entry = Entry(self.frame_distances)
        self.distance_jaw_entry.grid(row=1, column=1)
        self.distance_jaw_entry.configure(state='disabled')
        
        self.distance_chin = Label(self.frame_distances, text = "Kin - hals:")
        self.distance_chin.grid(row=2, column=0)
        self.distance_chin_entry = Entry(self.frame_distances)
        self.distance_chin_entry.grid(row=2, column=1)
        self.distance_chin_entry.configure(state='disabled')

        self.canvas_mouth.tag_bind("token", "<ButtonPress-1>", self.drag_start)
        self.canvas_mouth.tag_bind("token", "<ButtonRelease-1>", self.drag_stop)
        self.canvas_mouth.tag_bind("token", "<B1-Motion>", self.drag)
        self.canvas_side.tag_bind("token", "<ButtonPress-1>", self.drag_start)
        self.canvas_side.tag_bind("token", "<ButtonRelease-1>", self.drag_stop)
        self.canvas_side.tag_bind("token", "<B1-Motion>", self.drag)
        self.drag_data_mouth = {"x": 0, "y": 0, "item": None}
        self.drag_data_side = {"x": 0, "y": 0, "item": None}          

        
    def load(self):
        self.status = Label(self.parent, text="Status = OK", bd=1, relief=SUNKEN, anchor=W)
        self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
         
        self.filename = filedialog.askopenfilename(initialdir = os.getcwd(), title = 'Selecteer foto', filetypes=[('image files', ('.png','.jpg','.jpeg'))])
        if not self.filename:
            self.status = Label(self.parent, text="Geen afbeelding ingeladen", bd=1, relief=SUNKEN, anchor=W, fg='red')
            self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
        else:
            position = self.position.get()
            
            if position == "Mond open":
                self.reset_referentie()
                self.reset_distances()
                self.canvas_mouth.delete('all')        
                self.orig_image_mouth = Image.open(self.filename)               
                self.orig_image_mouth = ImageOps.exif_transpose(self.orig_image_mouth)
                if self.orig_image_mouth.size[0] > self.orig_image_mouth.size[1]: #landscape mode (breedte > lengte)
                    self.photomode = "Landschap"
                    self.img_height = 2200
                    height_percent = (self.img_height/float(self.orig_image_mouth.size[1]))    
                    self.img_width = int((float(self.orig_image_mouth.size[0])*float(height_percent)))
                    
                else:
                    self.photomode = "Portret"
                    self.img_height = 2200
                    height_percent = (self.img_height/float(self.orig_image_mouth.size[1]))    
                    self.img_width = int((float(self.orig_image_mouth.size[0])*float(height_percent)))

                self.image_mouth = ImageTk.PhotoImage(self.orig_image_mouth.resize((self.img_width, self.img_height), Image.NEAREST))
                self.canvas_image_mouth = self.canvas_mouth.create_image(self.img_width/2, self.img_height/2, image=self.image_mouth, tags = ("token"))
                self.canvas_mouth.grid()
                
                image = io.imread(self.filename)
                self.image_resized_mouth = np.asarray(transform.resize(image, (self.img_height, self.img_width, 3))*255, dtype=np.uint8)
                self.image_mouth_coords_initial = self.canvas_mouth.coords("token")

                
            elif position == "Rechts" or position == "Links":
                self.reset_referentie()
                self.reset_distances()
                
                self.canvas_side.delete('all')              
                self.orig_image_side = Image.open(self.filename)              
                self.orig_image_side = ImageOps.exif_transpose(self.orig_image_side)
                if self.orig_image_side.size[0] > self.orig_image_side.size[1]: #landscape mode (breedte > lengte)
                    self.photomode = "Landschap"
                    self.img_width = 2200
                    width_percent = (self.img_width/float(self.orig_image_side.size[0]))    
                    self.img_height = int((float(self.orig_image_side.size[1])*float(width_percent)))  
    
                else:
                    self.photomode = "Portret"
                    self.img_height = 2200
                    height_percent = (self.img_height/float(self.orig_image_side.size[1]))    
                    self.img_width = int((float(self.orig_image_side.size[0])*float(height_percent)))  
                    
                self.image_side = ImageTk.PhotoImage(image=self.orig_image_side.resize((self.img_width, self.img_height), Image.NEAREST))
                self.canvas_image_side = self.canvas_side.create_image(self.img_width/2, self.img_height/2, image=self.image_side, tags = ("token"))
                self.canvas_side.grid()
                
                image = io.imread(self.filename)
                self.image_resized_side = np.asarray(transform.resize(image, (self.img_height, self.img_width, 3))*255, dtype=np.uint8)
                self.image_side_coords_initial = self.canvas_side.coords("token")
                

                
    def reset_photo(self):
        position = self.position.get()
        
        if position == "Mond open":
            self.canvas_mouth.delete('all')
        if position == "Rechts" or position == "Links":
            self.canvas_side.delete('all')
            
        
    def predict(self):
        if self.filename == None:
            self.status = Label(self.parent, text="Geen afbeelding ingeladen", bd=1, relief=SUNKEN, anchor=W, fg='red')
            self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
        else:
            self.status = Label(self.parent, text="Status = OK", bd=1, relief=SUNKEN, anchor=W)
            self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
            
            position = self.position.get()
            
            if position == "Mond open":
                image_coords = self.canvas_mouth.coords("token")
                y_dif = self.image_mouth_coords_initial[0] - image_coords[0]
                x_dif = self.image_mouth_coords_initial[1] - image_coords[1]

                fa_sfd = face_alignment.FaceAlignment(face_alignment.LandmarksType._2D, device = 'cpu', flip_input=False, face_detector='sfd')
                self.preds_sfd_mouth = fa_sfd.get_landmarks(self.image_resized_mouth)
                if self.preds_sfd_mouth == None:
                    self.status = Label(self.parent, text="Geen gezicht gevonden", bd=1, relief=SUNKEN, anchor=W, fg='red')
                    self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)            
                else:
                    for idx in range(len(self.preds_sfd_mouth[0])): 
                        self.canvas_mouth.create_oval(self.preds_sfd_mouth[0][idx,0]-y_dif, self.preds_sfd_mouth[0][idx,1]-x_dif, self.preds_sfd_mouth[0][idx,0]+3-y_dif, self.preds_sfd_mouth[0][idx,1]+3-x_dif, fill='red', tags = ("face"))
            
            elif position == "Rechts" or position == "Links":
                image_coords = self.canvas_side.coords("token")
                y_dif = self.image_side_coords_initial[0] - image_coords[0]
                x_dif = self.image_side_coords_initial[1] - image_coords[1]
                                
                fa_sfd = face_alignment.FaceAlignment(face_alignment.LandmarksType._2D, device = 'cpu', flip_input=False, face_detector='sfd')
                self.preds_sfd_side = fa_sfd.get_landmarks(self.image_resized_side)
                if self.preds_sfd_side == None:
                    self.status = Label(self.parent, text="Geen gezicht gevonden", bd=1, relief=SUNKEN, anchor=W, fg='red')
                    self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)            
                else:
                    for idx in range(len(self.preds_sfd_side[0])): 
                        self.canvas_side.create_oval(self.preds_sfd_side[0][idx,0]-y_dif, self.preds_sfd_side[0][idx,1]-x_dif, self.preds_sfd_side[0][idx,0]+3-y_dif, self.preds_sfd_side[0][idx,1]+3-x_dif, fill='red', tags = ("face"))   
    
    def get_coords(self, event):
        self.x_ref = event.x
        self.y_ref = event.y
        
    def get_referentie_object(self):
        position = self.position.get()
        if position == "Mond open":
            self.canvas_mouth.bind("<Button 1>", self.get_coords)   
        elif position == "Rechts" or position == "Links":
            self.canvas_side.bind("<Button 1>", self.get_coords)
        
    def visualize_referentie(self):
        if self.x_ref is None:
            self.status = Label(self.parent, text="Klik op referentie object en klik opnieuw op knop", bd=1, relief=SUNKEN, anchor=W, fg='red')
            self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
            self.get_referentie_object()
        if not self.x_ref is None:
            position = self.position.get()
            
            if position == "Mond open":
                self.status = Label(self.parent, text="Status = OK", bd=1, relief=SUNKEN, anchor=W)
                self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
                
                image_coords = self.canvas_mouth.coords("token")
                y_dif = self.image_mouth_coords_initial[0] - image_coords[0]
                x_dif = self.image_mouth_coords_initial[1] - image_coords[1]
                
                y_ref = self.x_ref + y_dif
                x_ref = self.y_ref + x_dif
                
                self.mask = segmentation.flood(self.image_resized_mouth[:,:,0], (int(x_ref), int(y_ref)),tolerance = 5)
                self.ref_mask_mouth = np.argwhere(self.mask)
                self.ref1_m = self.canvas_mouth.create_oval(min(self.ref_mask_mouth[:,1])-2-y_dif, min(self.ref_mask_mouth[:,0])-2-x_dif, min(self.ref_mask_mouth[:,1])+2-y_dif, min(self.ref_mask_mouth[:,0])+2-x_dif, fill = 'blue')
                self.ref2_m = self.canvas_mouth.create_oval(min(self.ref_mask_mouth[:,1])-2-y_dif, max(self.ref_mask_mouth[:,0])-2-x_dif, min(self.ref_mask_mouth[:,1])+2-y_dif, max(self.ref_mask_mouth[:,0])+2-x_dif, fill = 'blue')
                self.ref3_m = self.canvas_mouth.create_oval(max(self.ref_mask_mouth[:,1])-2-y_dif, min(self.ref_mask_mouth[:,0])-2-x_dif, max(self.ref_mask_mouth[:,1])+2-y_dif, min(self.ref_mask_mouth[:,0])+2-x_dif, fill = 'blue')
                self.ref4_m = self.canvas_mouth.create_oval(max(self.ref_mask_mouth[:,1])-2-y_dif, max(self.ref_mask_mouth[:,0])-2-x_dif, max(self.ref_mask_mouth[:,1])+2-y_dif, max(self.ref_mask_mouth[:,0])+2-x_dif, fill = 'blue')
    
            elif position == "Rechts" or position == "Links":
                self.status = Label(self.parent, text="Status = OK", bd=1, relief=SUNKEN, anchor=W)
                self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
                
                image_coords = self.canvas_side.coords("token")
                y_dif = self.image_side_coords_initial[0] - image_coords[0]
                x_dif = self.image_side_coords_initial[1] - image_coords[1]
                
                y_ref = self.x_ref + y_dif
                x_ref = self.y_ref + x_dif
                
                self.mask = segmentation.flood(self.image_resized_side[:,:,0], (int(x_ref), int(y_ref)),tolerance = 20)

                self.ref_mask_side = np.argwhere(self.mask)
                self.ref1_s = self.canvas_side.create_oval(min(self.ref_mask_side[:,1])-2-y_dif, min(self.ref_mask_side[:,0])-2-x_dif, min(self.ref_mask_side[:,1])+2-y_dif, min(self.ref_mask_side[:,0])+2-x_dif, fill = 'blue')
                self.ref2_s = self.canvas_side.create_oval(min(self.ref_mask_side[:,1])-2-y_dif, max(self.ref_mask_side[:,0])-2-x_dif, min(self.ref_mask_side[:,1])+2-y_dif, max(self.ref_mask_side[:,0])+2-x_dif, fill = 'blue')
                self.ref3_s = self.canvas_side.create_oval(max(self.ref_mask_side[:,1])-2-y_dif, min(self.ref_mask_side[:,0])-2-x_dif, max(self.ref_mask_side[:,1])+2-y_dif, min(self.ref_mask_side[:,0])+2-x_dif, fill = 'blue')
                self.ref4_s = self.canvas_side.create_oval(max(self.ref_mask_side[:,1])-2-y_dif, max(self.ref_mask_side[:,0])-2-x_dif, max(self.ref_mask_side[:,1])+2-y_dif, max(self.ref_mask_side[:,0])+2-x_dif, fill = 'blue')
            
            
            
    def reset_referentie(self):
        self.x_ref = None
        position = self.position.get()
        
        if position == "Mond open":                
            self.canvas_mouth.delete(self.ref1_m)
            self.canvas_mouth.delete(self.ref2_m)
            self.canvas_mouth.delete(self.ref3_m)
            self.canvas_mouth.delete(self.ref4_m)
            self.ref_mask_mouth = None

            
        if position == "Rechts" or position == "Links":
            self.canvas_side.delete(self.ref1_s)
            self.canvas_side.delete(self.ref2_s)
            self.canvas_side.delete(self.ref3_s)
            self.canvas_side.delete(self.ref4_s) 
            self.ref_mask_side = None
            
    def reset_points(self):
        position = self.position.get()
        
        if position == "Mond open":
            self.canvas_mouth.delete("face")
        if position == "Rechts" or position == "Links":
            self.canvas_side.delete("face")
    
    def get_pixel_dist(self):
        position = self.position.get()
        if position == "Mond open":
            ref_mask = self.ref_mask_mouth
        elif position == "Rechts" or position == "Links":
            ref_mask = self.ref_mask_side
            
        reference_size = float(self.reference_size_entry.get())
            
        y_dist = (np.max(ref_mask[:,0]) - np.min(ref_mask[:,0]))/reference_size
        x_dist = (np.max(ref_mask[:,1]) - np.min(ref_mask[:,1]))/reference_size

        if y_dist == x_dist:
            self.pixel_dist = y_dist
        else:
            self.pixel_dist = max(y_dist, x_dist)
        
            
    def distances(self):
        position = self.position.get()
        if self.filename == None:
           self.status = Label(self.parent, text="Geen afbeelding ingeladen", bd=1, relief=SUNKEN, anchor=W, fg='red')
           self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
        if position == "Rechts":
            if self.ref_mask_side is None:
               self.status = Label(self.parent, text="Geen referentie object geselecteerd", bd=1, relief=SUNKEN, anchor=W, fg='red')
               self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
            elif self.preds_sfd_side == None:
               self.status = Label(self.parent, text="Geen gezichtspunten voorspeld", bd=1, relief=SUNKEN, anchor=W, fg='red')
               self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)       
            elif not len(self.distance_jaw_entry.get()) == 0:
                self.status = Label(self.parent, text="Al afstanden berekend - Reset afstanden", bd=1, relief=SUNKEN, anchor=W, fg='red')
                self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)      
            else:
                self.status = Label(self.parent, text="Status = OK", bd=1, relief=SUNKEN, anchor=W)
                self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)                
                self.get_pixel_dist()
 
                image_coords = self.canvas_side.coords("token")
                y_dif = self.image_side_coords_initial[0] - image_coords[0]
                x_dif = self.image_side_coords_initial[1] - image_coords[1]
                
                point_10 = self.preds_sfd_side[0][9]
                point_4 = self.preds_sfd_side[0][3]
                y = [point_10[0], point_4[0]]
                x = [point_10[1], point_4[1]]
                four_ten_pix = np.sqrt((point_4[0]-point_10[0])**2 + (point_4[1]-point_10[1])**2)
                four_ten_cm = round(four_ten_pix/self.pixel_dist, 1)
                self.line1 = self.canvas_side.create_line(y[0]-y_dif, x[0]-x_dif, y[1]-y_dif, x[1]-x_dif, fill = 'blue')  
                self.distance_jaw_entry.configure(state='normal')
                self.distance_jaw_entry.insert(0, four_ten_cm)
                self.distance_jaw_entry.configure(state='disabled')
                 
                point_6 = self.preds_sfd_side[0][5]
                point_10 = self.preds_sfd_side[0][9]
                y = [point_10[0], point_6[0]]
                x = [point_10[1], point_6[1]]
                six_ten_pix = np.sqrt((point_6[0]-point_10[0])**2 + (point_6[1]-point_10[1])**2)
                six_ten_cm = round(six_ten_pix/self.pixel_dist, 1)
                self.line2 = self.canvas_side.create_line(y[0]-y_dif, x[0]-x_dif, y[1]-y_dif, x[1]-x_dif, fill = 'blue')
                self.distance_chin_entry.configure(state='normal')
                self.distance_chin_entry.insert(0, six_ten_cm)
                self.distance_chin_entry.configure(state='disabled')
                
        if position == "Links":
            if self.preds_sfd_side == None:
               self.status = Label(self.parent, text="Geen gezichtspunten voorspeld", bd=1, relief=SUNKEN, anchor=W, fg='red')
               self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)       
            elif not len(self.distance_jaw_entry.get()) == 0:
                self.status = Label(self.parent, text="Al afstanden berekend - Reset afstanden", bd=1, relief=SUNKEN, anchor=W, fg='red')
                self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)      
            else:
                self.status = Label(self.parent, text="Status = OK", bd=1, relief=SUNKEN, anchor=W)
                self.status.grid(row=6, column=0, columnspan=2, sticky=W+E) 
                self.get_pixel_dist()
                
                image_coords = self.canvas_side.coords("token")
                y_dif = self.image_side_coords_initial[0] - image_coords[0]
                x_dif = self.image_side_coords_initial[1] - image_coords[1]
                
                point_8 = self.preds_sfd_side[0][7]
                point_14 = self.preds_sfd_side[0][13]
                y = [point_8[0], point_14[0]]
                x = [point_8[1], point_14[1]]   
                eight_fourteen_pix = np.sqrt((point_8[0]-point_14[0])**2 + (point_8[1]-point_14[1])**2)
                eight_fourteen_cm = round(eight_fourteen_pix/self.pixel_dist, 1)
                
                
                self.line1 = self.canvas_side.create_line(y[0]-y_dif, x[0]-x_dif, y[1]-y_dif, x[1]-x_dif, fill = 'blue')  
                self.distance_jaw_entry.configure(state='normal')
                self.distance_jaw_entry.insert(0, eight_fourteen_cm)
                self.distance_jaw_entry.configure(state='disabled')
                 
                point_12 = self.preds_sfd_side[0][11]
                point_8 = self.preds_sfd_side[0][7]
                y = [point_8[0], point_12[0]]
                x = [point_8[1], point_12[1]]
                eight_twelve_pix = np.sqrt((point_12[0]-point_8[0])**2 - (point_12[1]-point_8[1])**2)
                
                eight_twelve_cm = round(eight_twelve_pix/self.pixel_dist, 1)

                self.line2 = self.canvas_side.create_line(y[0]-y_dif, x[0]-x_dif, y[1]-y_dif, x[1]-x_dif, fill = 'blue')
                self.distance_chin_entry.configure(state='normal')
                self.distance_chin_entry.insert(0, eight_twelve_cm)
                self.distance_chin_entry.configure(state='disabled')

                 
        if position == "Mond open":
            if self.ref_mask_mouth is None:
               self.status = Label(self.parent, text="Geen referentie object geselecteerd", bd=1, relief=SUNKEN, anchor=W, fg='red')
               self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
            elif self.preds_sfd_mouth == None:
               self.status = Label(self.parent, text="Geen gezichtspunten voorspeld", bd=1, relief=SUNKEN, anchor=W, fg='red')
               self.status.grid(row=6, column=0, columnspan=2, sticky=W+E) 
            elif not len(self.distance_mouth_entry.get()) == 0:
                self.status = Label(self.parent, text="Al afstanden berekend - Reset afstanden", bd=1, relief=SUNKEN, anchor=W, fg='red')
                self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)  
            else: 
                self.status = Label(self.parent, text="Status = OK", bd=1, relief=SUNKEN, anchor=W)
                self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)
                self.get_pixel_dist()
                
                image_coords = self.canvas_mouth.coords("token")
                y_dif = self.image_mouth_coords_initial[0] - image_coords[0]
                x_dif = self.image_mouth_coords_initial[1] - image_coords[1]
                
                point_63 = self.preds_sfd_mouth[0][62]
                point_67 = self.preds_sfd_mouth[0][66]
                y = [point_63[0], point_67[0]]
                x = [point_67[1], point_63[1]]
                sixthree_sixseven_pix = abs(x[1] - x[0])
                sixthree_sixseven_cm = round(sixthree_sixseven_pix/self.pixel_dist, 1)
                self.line3= self.canvas_mouth.create_line(y[0]-y_dif, x[0]-x_dif, y[0]-y_dif, x[1]-x_dif, fill = 'blue')
                self.distance_mouth_entry.configure(state='normal')
                self.distance_mouth_entry.insert(0, sixthree_sixseven_cm)
                self.distance_mouth_entry.configure(state='disabled')
              
    def reset_distances_all(self):
        self.status = Label(self.parent, text="Status = OK", bd=1, relief=SUNKEN, anchor=W)
        self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)        
        self.x_ref = None       
        self.canvas_side.delete(self.line1)
        self.canvas_side.delete(self.line2)
        self.canvas_mouth.delete(self.line3)
        self.distance_chin_entry.configure(state='normal')
        self.distance_chin_entry.delete(0,'end')
        self.distance_chin_entry.configure(state='disabled')
        self.distance_jaw_entry.configure(state='normal')
        self.distance_jaw_entry.delete(0, 'end')
        self.distance_jaw_entry.configure(state='disabled')
        self.distance_mouth_entry.configure(state='normal')
        self.distance_mouth_entry.delete(0,'end')
        self.distance_mouth_entry.configure(state='disabled')  
   
    def reset_distances(self):
        position = self.position.get()
        self.status = Label(self.parent, text="Status = OK", bd=1, relief=SUNKEN, anchor=W)
        self.status.grid(row=6, column=0, columnspan=2, sticky=W+E)        
        self.x_ref = None       
        
        if position == "Mond open":            
            self.canvas_mouth.delete(self.line3)
            self.distance_mouth_entry.configure(state='normal')
            self.distance_mouth_entry.delete(0,'end')
            self.distance_mouth_entry.configure(state='disabled')     
        if position == "Rechts" or position == "Links":
            self.canvas_side.delete(self.line1)
            self.canvas_side.delete(self.line2)
            self.distance_chin_entry.configure(state='normal')
            self.distance_chin_entry.delete(0,'end')
            self.distance_chin_entry.configure(state='disabled')
            self.distance_jaw_entry.configure(state='normal')
            self.distance_jaw_entry.delete(0, 'end')
            self.distance_jaw_entry.configure(state='disabled')            
    
        
    def drag_start(self, event):
        position = self.position.get()
        if position == "Mond open":
            self.drag_data_mouth["item"] = self.canvas_image_mouth
            self.drag_data_mouth["x"] = event.x
            self.drag_data_mouth["y"] = event.y
        if position == "Rechts" or position == "Links":
            self.drag_data_side["item"] = self.canvas_image_side
            self.drag_data_side["x"] = event.x
            self.drag_data_side["y"] = event.y

    def drag_stop(self, event):
        position = self.position.get()
        if position == "Mond open":
            self.drag_data_mouth["item"] = None
            self.drag_data_mouth["x"] = 0
            self.drag_data_mouth["y"] = 0
        if position == "Rechts" or position == "Links":
            self.drag_data_side["item"] = None
            self.drag_data_side["x"] = 0
            self.drag_data_side["y"] = 0
            
    def drag(self, event):
        position = self.position.get()
        if position == "Mond open":
            delta_x = event.x - self.drag_data_mouth["x"]
            delta_y = event.y - self.drag_data_mouth["y"]
            self.canvas_mouth.move(self.canvas_image_mouth, delta_x, delta_y)
            self.drag_data_mouth["x"] = event.x
            self.drag_data_mouth["y"] = event.y
        if position == "Rechts" or position == "Links":
            delta_x = event.x - self.drag_data_side["x"]
            delta_y = event.y - self.drag_data_side["y"]
            self.canvas_side.move(self.canvas_image_side, delta_x, delta_y)
            self.drag_data_side["x"] = event.x
            self.drag_data_side["y"] = event.y            
            

if __name__ == '__main__':
    root = Tk()
    root.title('GUI Gezichtsherkenning - Referentie Object')
    root.geometry("1600x800")
    top = MyWindow(root)
    root.mainloop()