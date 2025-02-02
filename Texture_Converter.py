
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import *
from PIL import Image, ImageTk
import numpy as np


# Variable to track the imported normal map type
normal_map_type = "directx"


# _co Mode
def set_co_conversion_mode(mode):
    global co_conversion_mode
    co_conversion_mode.set(mode)
    
    # Refresh Button-Stile
    if mode == "base_color":
        base_color_button.configure(relief=tk.SUNKEN, bg="lightblue")
        base_color_specular_button.configure(relief=tk.RAISED, bg="SystemButtonFace")
    elif mode == "base_color_specular":
        base_color_specular_button.configure(relief=tk.SUNKEN, bg="lightblue")
        base_color_button.configure(relief=tk.RAISED, bg="SystemButtonFace")

# convert _co texture
def convert_co_texture(base_color_path, metal_path, output_path, use_specular_conversion=False):
    try:
        base_color = Image.open(base_color_path).convert("RGB")

        if use_specular_conversion and metal_path:
            metal_map = Image.open(metal_path).convert("L")

           # Numpy arrays for the calculation
            base_color_np = np.array(base_color, dtype=np.float32) / 255.0
            metal_map_np = np.array(metal_map, dtype=np.float32) / 255.0

            # Calculate specula color
            specular_color_np = base_color_np * metal_map_np[..., None] + (1 - metal_map_np[..., None]) * 0.04
            specular_factor_np = np.max(specular_color_np, axis=2, keepdims=True)

            #Calculate diffuse paint
            diffuse_color_np = base_color_np * (1 - specular_factor_np)

            # Scali back to 0-255 and save
            diffuse_color_img = Image.fromarray((diffuse_color_np * 255).astype(np.uint8))
            diffuse_color_img.save(output_path, format="TGA")
            print(f"_co successfully saved with Specular correction under {output_path}")

        else:
            base_color.save(output_path, format="TGA")
            print(f"_co successfully saved as Base Color only under {output_path}")

        return output_path

    except Exception as e:
        print(f"Error when creating the _co texture: {e}")
        return None

# convert _as texture
def convert_as_texture(ao_path, output_path):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Load AO-Textur and convert into grayscale
        ao = Image.open(ao_path).convert("L")

        # First inversion of the AO -Map (255 - value)e)
        inverted_ao = Image.eval(ao, lambda x: 255 - x)

        # Black channels for R&B (0)
        black_channel = Image.new("L", ao.size, 0)

        # Combine to an RGB texture (_AS) with (r = 0, g = inverted AO, B = 0)
        as_texture = Image.merge("RGB", (black_channel, inverted_ao, black_channel))

        # Second inversion of the entire _AS texture
        final_as_texture = Image.eval(as_texture, lambda x: 255 - x)

        # Save as .tga
        final_as_texture.save(output_path, format="TGA")
        print(f"_as successfully saved under {output_path}")
        return output_path
    except Exception as e:
        print(f"Error when creating the _as texture: {e}")
        return None

# convert _nohq texture
def convert_nohq_texture(normal_path, output_path, normal_map_type):
    try:
        # Open Normal Map image
        normal_map = Image.open(normal_path).convert("RGB")

        # Adjust for DirectX or OpenGL
        if normal_map_type == "directx":
            # DirectX flips the green channel
            r, g, b = normal_map.split()
            g = Image.eval(g, lambda x: 255 - x)
            normal_map = Image.merge("RGB", (r, g, b))

        # Save as _nohq texture
        normal_map.save(output_path, format="TGA")
        print(f"_nohq successfully saved under {output_path}")
        return output_path
    except Exception as e:
        print(f"Error when creating the _nohq texture: {e}")
        return None

# metallic to specular
def metallic_to_specular(metallic, base_color, specular_factor):
    """
    Berechnet die Specular-Farbe aus Metallic und Base Color mit einstellbarem Specular-Faktor.
    """
    return [min(255, max(0, int((base_color[i] * metallic + (1 - metallic) * 0.04) * specular_factor * 255))) for i in range(3)]

# convert _smdi texture
def convert_smdi_texture(metal_path, roughness_path, output_path, specular_factor=0.75, glossiness_factor=1.0):
    try:
        if not (metal_path and roughness_path):
            raise ValueError("Metallic- oder Roughness-Dateipfad fehlt.")
        
        metallic_image = Image.open(metal_path).convert("L")
        roughness_image = Image.open(roughness_path).convert("L")
        
        #Calculate the specular from metallic and adjust it with Specular factor
        specular_image = Image.eval(metallic_image, lambda x: int(metallic_to_specular(x / 255.0, [1.0, 1.0, 1.0], specular_factor)[1]))
        
        # Calculate glossiness and adjust with glossiness factor
        glossiness_image = Image.eval(roughness_image, lambda x: int((255 - x) * glossiness_factor))
        
        red_channel = Image.new("L", metallic_image.size, 255)  # Completely white
        green_channel = specular_image  # Specular value
        blue_channel = glossiness_image  # Glossiness
        
        smdi_map = Image.merge("RGB", (red_channel, green_channel, blue_channel))
        smdi_map.save(output_path, format="TGA")
        
        print(f"_smdi successfully saved under {output_path}")
        return output_path
    except Exception as e:
        print(f"Error when creating the _smdi texture: {e}")
        return None



# Show large preview
def show_large_preview(file_path):
    try:
        preview_window = tk.Toplevel(root)
        preview_window.title("Preview")
        preview_window.geometry("1024x1024")

        img = Image.open(file_path)
        img = img.resize((1024, 1024))  # Resize to 1024x1024
        img_tk = ImageTk.PhotoImage(img)

        label = tk.Label(preview_window, image=img_tk)
        label.image = img_tk  # Keep a reference to avoid garbage collection
        label.pack(expand=True, fill=tk.BOTH)
    except Exception as e:
        print(f"Error showing large preview: {e}")

# Start conversion
def start_conversion():
    global active_button
    output_folder = output_entry.get()
    prefix = prefix_entry.get()

    if not output_folder:
        messagebox.showerror("Error", "Output folder must be selected.")
        return

    try:
        base_color_path = base_color_entry.get()
        metal_path = metal_entry.get()
        co_output = os.path.join(output_folder, f"{prefix}_co.tga")

        # Call mode from the button selection
        use_specular = (co_conversion_mode.get() == "base_color_specular")

        if base_color_path:
            convert_co_texture(base_color_path, metal_path, co_output, use_specular)
            update_preview(base_color_result_label, co_output)
        else:
            print("Error: Base Color fehlt für _co Konvertierung")
    except Exception as e:
        print(f"Error in _co conversion: {e}")

    # ✅ Now the other conversions in separate try blocks follow

    try:
        ao_path = ao_entry.get()
        as_output = os.path.join(output_folder, f"{prefix}_as.tga")
        if ao_path:
            convert_as_texture(ao_path, as_output)
            update_preview(as_result_label, as_output)
    except Exception as e:
        print(f"Error in _as conversion: {e}")

    try:
        normal_path = normal_entry.get()
        nohq_output = os.path.join(output_folder, f"{prefix}_nohq.tga")
        if normal_path:
            convert_nohq_texture(normal_path, nohq_output, normal_map_type)
            update_preview(normal_result_label, nohq_output)
    except Exception as e:
        print(f"Error in _nohq conversion: {e}")

    try:
        roughness_path = roughness_entry.get()
        smdi_output = os.path.join(output_folder, f"{prefix}_smdi.tga")
        specular_factor = specular_scale.get()
        glossiness_factor = glossiness_scale.get()
        
        if metal_path and roughness_path:
            convert_smdi_texture(metal_path, roughness_path, smdi_output, specular_factor, glossiness_factor)
            update_preview(smdi_result_label, smdi_output)
    except Exception as e:
        print(f"Error in _smdi conversion: {e}")

    print("✅ Conversion process completed!")

# Select file
def select_file(entry, preview_label):
    file_path = filedialog.askopenfilename(title="Select File", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.tga")])
    if file_path:
        entry.delete(0, tk.END)
        entry.insert(0, file_path)

        try:
            # Load the image and ensure it is in a compatible mode
            img = Image.open(file_path)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            
            # Resize for smaller preview
            img.thumbnail((130, 130))
            img_tk = ImageTk.PhotoImage(img)

            # Update the preview label
            preview_label.configure(image=img_tk, width=130, height=130)
            preview_label.image = img_tk  # Keep a reference to avoid garbage collection
        except Exception as e:
            print(f"Error loading image: {e}")
            preview_label.configure(image=None, width=130, height=130, text="Error")

# Select output folder
def select_output_folder():
    folder_selected = filedialog.askdirectory()
    output_entry.delete(0, tk.END)
    output_entry.insert(0, folder_selected)

# Update preview
def update_preview(label, file_path):
    try:
        img = Image.open(file_path)
        img.thumbnail((130, 130))
        img_tk = ImageTk.PhotoImage(img)
        label.configure(image=img_tk, width=130, height=130)
        label.image = img_tk  # Important: Save the reference
        label.bind("<Button-1>", lambda e: show_large_preview(file_path))
    except Exception as e:
        print(f"Fehler beim Laden der Vorschau: {e}")
        label.configure(image=None, width=130, height=130, text="Fehler")


def set_normal_map_type(type):
    global normal_map_type
    normal_map_type = type
    print(f"Normal map type set to: {type}")

    # Update button styles
    if type == "directx":
        directx_button.configure(relief=tk.SUNKEN, bg="lightblue")
        opengl_button.configure(relief=tk.RAISED, bg="SystemButtonFace")
    elif type == "opengl":
        opengl_button.configure(relief=tk.SUNKEN, bg="lightblue")
        directx_button.configure(relief=tk.RAISED, bg="SystemButtonFace")


# Create the GUI
root  = tk.Tk()
root .title("Texture Converter 0.87b")
root .geometry("750x800")


  
label2 = Label( root, text = "RwG Texture Converter", font = ("Helvetica", 20))
label2.pack(pady = 50) 

Texture_Input_frame = tk.Frame(root)
Texture_Input_frame.pack(pady=10)


base_color_label = tk.Label(Texture_Input_frame, text="Base Color:")
base_color_label.grid(row=0, column=0, padx=5)
base_color_entry = tk.Entry(Texture_Input_frame, width=21)
base_color_entry.grid(row=1, column=0, padx=5)
base_color_preview = tk.Label(Texture_Input_frame, text="Base Color:", width=18, height=9, bg="gray", )
base_color_preview.grid(row=2, column=0, padx=5)
base_color_button = tk.Button(Texture_Input_frame, text="Browse", command=lambda: select_file(base_color_entry, base_color_preview))
base_color_button.grid(row=3, column=0, padx=5)

base_color_convert_button = tk.Button(Texture_Input_frame, text="Base Color Only", command=lambda: set_co_conversion_mode("base_color"))
base_color_convert_button.grid(row=4, column=0, padx=5)

base_color_specular_button = tk.Button(Texture_Input_frame, text="Base Color + Specular",  command=lambda: set_co_conversion_mode("base_color_specular"))
base_color_specular_button.grid(row=5, column=0, padx=5)




normal_label = tk.Label(Texture_Input_frame, text="Normal Map:")
normal_label.grid(row=0, column=1, padx=5)
normal_entry = tk.Entry(Texture_Input_frame, width=21)
normal_entry.grid(row=1, column=1, padx=5)
normal_preview = tk.Label(Texture_Input_frame, width=18, text="Normal Map:", height=9, bg="gray")
normal_preview.grid(row=2, column=1, padx=5)
normal_button = tk.Button(Texture_Input_frame, text="Browse", command=lambda: select_file(normal_entry, normal_preview))
normal_button.grid(row=3, column=1, padx=5)

directx_button = tk.Button(Texture_Input_frame, text="DirectX", command=lambda: set_normal_map_type("directx"))
directx_button.grid(row=4, column=1, padx=5)
opengl_button = tk.Button(Texture_Input_frame, text="OpenGL", command=lambda: set_normal_map_type("opengl"))
opengl_button.grid(row=5, column=1, padx=5)

roughness_label = tk.Label(Texture_Input_frame, text="Roughness:")
roughness_label.grid(row=0, column=2, padx=5)
roughness_entry = tk.Entry(Texture_Input_frame, width=21)
roughness_entry.grid(row=1, column=2, padx=5)
roughness_preview = tk.Label(Texture_Input_frame, width=18, height=9, text="Roughness:", bg="gray")
roughness_preview.grid(row=2, column=2, padx=5)
roughness_button = tk.Button(Texture_Input_frame, text="Browse", command=lambda: select_file(roughness_entry, roughness_preview))
roughness_button.grid(row=3, column=2, padx=5)

metal_label = tk.Label(Texture_Input_frame, text="Metal:")
metal_label.grid(row=0, column=3, padx=5)
metal_entry = tk.Entry(Texture_Input_frame, width=21)
metal_entry.grid(row=1, column=3, padx=5)
metal_preview = tk.Label(Texture_Input_frame, width=18, height=9, text="Metal:", bg="gray")
metal_preview.grid(row=2, column=3, padx=5)
metal_button = tk.Button(Texture_Input_frame, text="Browse", command=lambda: select_file(metal_entry, metal_preview))
metal_button.grid(row=3, column=3, padx=5)

ao_label = tk.Label(Texture_Input_frame, text="AO Map:")
ao_label.grid(row=0, column=4, padx=5)
ao_entry = tk.Entry(Texture_Input_frame, width=21)
ao_entry.grid(row=1, column=4, padx=5)
ao_preview = tk.Label(Texture_Input_frame, width=18, text="AO Map:", height=9, bg="gray")
ao_preview.grid(row=2, column=4, padx=5)
ao_button = tk.Button(Texture_Input_frame, text="Browse", command=lambda: select_file(ao_entry, ao_preview))
ao_button.grid(row=3, column=4, padx=5)

Texture_Output_frame = tk.Frame(root)
Texture_Output_frame.pack(pady=10)
prefix_label = tk.Label(Texture_Output_frame, text="File Prefix:")
prefix_rvmat_label = tk.Label(Texture_Output_frame, text=".rvmat")
prefix_rvmat_label.grid (row=1, column=4, padx=0)
prefix_label.grid(row=0, column=3, padx=0)
prefix_entry = tk.Entry(Texture_Output_frame, width=25)
prefix_entry.grid(row=1, column=3, padx=0)

output_label = tk.Label(Texture_Output_frame, text="Output Folder:")
output_label.grid(row=0, column=1, padx=0)
output_entry = tk.Entry(Texture_Output_frame, width=60)
output_entry.grid(row=1, column=1, padx=0)
output_button = tk.Button(Texture_Output_frame, text="Browse", command=select_output_folder)
output_button.grid(row=1, column=0, pady=5)



# Start buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

general_conversion_button = tk.Button(button_frame, text="Start Conversion", command=start_conversion)
general_conversion_button.grid(row=1, column=0, columnspan=2, pady=10)



# Result previews
result_frame = tk.Frame(root)
result_frame.pack(pady=20)

base_color_result_label = tk.Label(result_frame, text="_co Result", activebackground="red", width=18, height=9, bg="gray")
base_color_result_label.grid(row=1, column=0, padx=10)

normal_result_label = tk.Label(result_frame, text="_nohq Result", width=18, height=9, bg="gray")
normal_result_label.grid(row=1, column=1, padx=10)

specular_scale = tk.Scale(result_frame, length=143, activebackground="red", from_=2.0, to=0, showvalue=1, resolution=0.05, orient=tk.VERTICAL)
specular_scale.set(0.75)
specular_scale.grid(row=1, column=2, padx=10)

glossiness_scale = tk.Scale(result_frame, length=143, activebackground="red",  showvalue=1, from_=2.0, to=0.0, resolution=0.05, orient=tk.VERTICAL)
glossiness_scale.set(1.0)
glossiness_scale.grid(row=1, column=3, padx=0)

smdi_result_label = tk.Label(result_frame, text="_smdi Result", width=18, height=9, bg="gray")
smdi_result_label.grid(row=1, column=4, padx=10)



as_result_label = tk.Label(result_frame, text="_as Result", width=18, height=9, bg="gray")
as_result_label.grid(row=1, column=5, padx=10)

co_label = tk.Label(result_frame, text="_co", bg="gray")
co_label.grid(row=0, column=0, padx=10)

nohq_label = tk.Label(result_frame, text="_nohq", bg="gray")
nohq_label.grid(row=0, column=1, padx=10)

spec_label = tk.Label(result_frame, width=5, text="Spec", bg="gray")
spec_label.grid(row=0, column=2, padx=10)

gloss_label = tk.Label(result_frame, width=5, text="Gloss", bg="gray")
gloss_label.grid(row=0, column=3, padx=10)

smdi_label = tk.Label(result_frame, text="_smdi", bg="gray")
smdi_label.grid(row=0, column=4, padx=10)

as_label = tk.Label(result_frame, text="_as", bg="gray")
as_label.grid(row=0, column=5, padx=10)



# Set default active button
set_normal_map_type("directx")

co_conversion_mode = tk.StringVar(value="base_color")  # Standard: Base Color Only

# Function to select the conversion mode
def set_co_conversion_mode(mode):
    global co_conversion_mode
    co_conversion_mode.set(mode)

    # Update button styles
    if mode == "base_color":
        base_color_convert_button.configure(relief=tk.SUNKEN, bg="lightblue")
        base_color_specular_button.configure(relief=tk.RAISED, bg="SystemButtonFace")
    elif mode == "base_color_specular":
        base_color_specular_button.configure(relief=tk.SUNKEN, bg="lightblue")
        base_color_convert_button.configure(relief=tk.RAISED, bg="SystemButtonFace")

set_co_conversion_mode("base_color")


root.mainloop()
