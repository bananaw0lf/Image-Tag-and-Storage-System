import base64
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import requests
import os
import json
class ImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pix-Tag - Application")

        # Upload Frame
        upload_frame = tk.Frame(root)
        upload_frame.pack(pady=10)

        tk.Label(upload_frame, text="Upload Image:").pack(side=tk.LEFT)
        tk.Button(upload_frame, text="upload", command=self.upload_image).pack(side=tk.LEFT)

        # Query Frame
        query_frame = tk.Frame(root)
        query_frame.pack(pady=10)

        tk.Label(query_frame, text="Query by Tags:").pack(side=tk.LEFT)
        tk.Button(query_frame, text="Search", command=self.query_images).pack(side=tk.LEFT)

        # Delete Frame
        delete_frame = tk.Frame(root)
        delete_frame.pack(pady=10)

        tk.Label(delete_frame, text="Delete Images:").pack(side=tk.LEFT)
        tk.Button(delete_frame, text="Delete", command=self.delete_images).pack(side=tk.LEFT)

        # Result Frame
        self.result_frame = tk.Frame(root)
        self.result_frame.pack(pady=10)

        tk.Label(self.result_frame, text="Results:").pack(side=tk.LEFT)
        self.result_text = tk.Text(self.result_frame, height=10, width=50)
        self.result_text.pack(side=tk.LEFT)

    def upload_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            try:
                with open(file_path, 'rb') as file:
                    image_data = base64.b64encode(file.read()).decode('utf-8')
                upload_api_endpoint = "https://bf9tbiuk94.execute-api.us-east-1.amazonaws.com/raw/api/upload"
                headers = {
                    'Content-Type': 'application/json'
                }
                payload = {
                    'body': json.dumps({
                        'image': image_data,
                        'file_name': file_name
                    })
                }
                response = requests.post(upload_api_endpoint, json=payload, headers=headers)
                response_data = response.json()

                if response_data.get('statusCode') == 200:
                    messagebox.showinfo("Success", f"Image {file_name} uploaded successfully!")
                else:
                    messagebox.showerror("Error", f"Failed to upload image {file_name}. Response: {response.text}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def query_images(self):
        tags = simpledialog.askstring("Tags", "Enter tags separated by commas:")
        if tags:
            tags_list = tags.split(',')
            try:
                # Simulate querying images
                self.result_text.delete('1.0', tk.END)
                self.result_text.insert(tk.END, "\n".join(f"Image with tag: {tag}" for tag in tags_list))
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def delete_images(self):
        image_urls = simpledialog.askstring("Image URLs", "Enter image URLs separated by commas:")
        if image_urls:
            urls_list = image_urls.split(',')
            try:
                # Simulate deleting images
                messagebox.showinfo("Success", f"Deleted Images: {', '.join(urls_list)}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageApp(root)
    root.mainloop()
