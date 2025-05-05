# storage_check.py - Check storage usage on Raspberry Pi Pico
import os
import gc

def format_size(size):
    """Format size in bytes to a human-readable format"""
    for unit in ['B', 'KB', 'MB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} MB"

def get_file_size(path):
    """Get size of a file"""
    try:
        stats = os.stat(path)
        return stats[6]  # Position 6 contains the file size
    except:
        return 0

def check_storage():
    """Check storage usage on the Pico"""
    print("\n--- Storage Usage Report ---\n")
    
    # Collect garbage to get accurate memory readings
    gc.collect()
    
    
    # Flash storage usage
    print("\nFlash Storage:")
    
    # Get the list of files and directories
    paths = []
    
    # Helper function to scan directories recursively
    def scan_dir(path):
        for entry in os.listdir(path):
            full_path = path + "/" + entry if path != "" else entry
            try:
                # Try to get directory contents - if it succeeds, it's a directory
                os.listdir(full_path)
                scan_dir(full_path)
            except:
                # It's a file
                paths.append(full_path)
    
    try:
        scan_dir("")
    except Exception as e:
        print(f"Error scanning directories: {e}")
    
    # Calculate total size and print file info
    total_size = 0
    
    # Sort files by size (largest first)
    file_sizes = [(path, get_file_size(path)) for path in paths]
    file_sizes.sort(key=lambda x: x[1], reverse=True)
    
    # Print the 15 largest files
    print("\n15 Largest Files:")
    print(f"{'Size':>10} | Path")
    print("-" * 50)
    
    for i, (path, size) in enumerate(file_sizes[:15]):
        print(f"{format_size(size):>10} | {path}")
        total_size += size
    
    # Directory sizes
    dir_sizes = {}
    for path, size in file_sizes:
        parts = path.split('/')
        current = ""
        for part in parts[:-1]:  # Exclude filename
            if current:
                current += "/" + part
            else:
                current = part
                
            if current in dir_sizes:
                dir_sizes[current] += size
            else:
                dir_sizes[current] = size
    
    # Print directory sizes
    print("\nDirectory Sizes:")
    print(f"{'Size':>10} | Directory")
    print("-" * 50)
    
    sorted_dirs = sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)
    for dir_path, size in sorted_dirs[:10]:  # Top 10 directories
        if dir_path == "":
            dir_path = "(root)"
        print(f"{format_size(size):>10} | {dir_path}")
    
    # Calculate remaining size for other files
    other_size = 0
    for _, size in file_sizes[15:]:
        other_size += size
    
    if other_size > 0:
        print(f"{format_size(other_size):>10} | (other files)")
    
    print(f"\nTotal file size: {format_size(total_size)}")
    
    # Font file analysis
    print("\nFont File Analysis:")
    font_files = [f for f in paths if f.endswith('.py') and ('font' in f.lower() or 'sans' in f.lower() or 'courier' in f.lower())]
    
    if font_files:
        print(f"{'Size':>10} | Font File")
        print("-" * 50)
        
        font_sizes = [(path, get_file_size(path)) for path in font_files]
        font_sizes.sort(key=lambda x: x[1], reverse=True)
        
        font_total = 0
        for path, size in font_sizes:
            print(f"{format_size(size):>10} | {path}")
            font_total += size
            
        print(f"\nTotal font file size: {format_size(font_total)} ({font_total / total_size * 100:.1f}% of all files)")
    else:
        print("No font files found.")
    
    # Free and allocated RAM
    free_ram = gc.mem_free()
    allocated_ram = gc.mem_alloc()
    total_ram = free_ram + allocated_ram
    
    print("\n")
    print(f"RAM USAGE:")
    print(f"  Free:       {format_size(free_ram)} ({free_ram / total_ram * 100:.1f}%)")
    print(f"  Used:       {format_size(allocated_ram)}") # ({allocated_ram / total_ram * 100:.1f}%)")
    print(f"  Total:      {format_size(total_ram)}")
    print(f"  Usage %:    {allocated_ram / total_ram * 100:.1f}%")
    
    # Calculate total flash size (2MB for Pico)
    # The Raspberry Pi Pico has 2MB (2,097,152 bytes) of flash storage
    total_flash = 2 * 1024 * 1024  # 2MB in bytes
    
    # Print summary of total storage usage
    print("\n")
    print("STORAGE USAGE:")
    print(f"  Free Space:    {format_size(total_flash - total_size)} ({(1 - total_size / total_flash) * 100:.1f}%)")
    print(f"  Total Used:    {format_size(total_size)}")
    print(f"  Total Avail:   {format_size(total_flash)}")
    print(f"  Usage %:       {total_size / total_flash * 100:.1f}%")

# Run the storage check
if __name__ == "__main__":
    check_storage()