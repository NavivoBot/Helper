import os

# مسیر پوشه assets
ASSETS_DIR = "assets"

# ساختار پوشه‌ها
folders = [
    "images",
    "images/modules",
    "images/ui",
    "audio",
    "fonts",
    "videos"
]

# فایل‌های placeholder
files = {
    "images": ["logo.png", "bot_avatar.png"],
    "images/modules": ["living.png", "transport.png", "health.png", "work.png", "offices.png"],
    "images/ui": ["button.png", "menu.png", "notification.png"],
    "audio": ["notification.mp3", "welcome.mp3", "error.mp3"],
    "fonts": ["Roboto-Regular.ttf", "Roboto-Bold.ttf"],
    "videos": ["intro.mp4"]
}

# ایجاد پوشه‌ها
for folder in folders:
    path = os.path.join(ASSETS_DIR, folder)
    os.makedirs(path, exist_ok=True)
    print(f"Created folder: {path}")

# ایجاد فایل‌های placeholder
for folder, file_list in files.items():
    for file_name in file_list:
        file_path = os.path.join(ASSETS_DIR, folder, file_name)
        # فایل placeholder خالی بساز
        with open(file_path, "wb") as f:
            f.write(b"")  # فایل خالی
        print(f"Created placeholder file: {file_path}")

print("\n✅ All assets folders and placeholder files are created!")
