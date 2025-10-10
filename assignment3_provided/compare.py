import os
import filecmp

# Hardcoded files to compare (edit as needed)
FILE_A = output_grid1_150_150_MP.txt
FILE_B = "output_grid1_575_575_MP.txt"

def main():
    a = FILE_A
    b = FILE_B

    if not os.path.exists(a):
        print(f"Missing file: {a}")
        return
    if not os.path.exists(b):
        print(f"Missing file: {b}")
        return

    # Compare file contents (not metadata)
    same = filecmp.cmp(a, b, shallow=False)
    print(f"Comparing:\n  {a}\n  {b}")
    if same:
        print("Files are the same")
    else:
        print("Files are NOT the same")

if __name__ == "__main__":
    main()
