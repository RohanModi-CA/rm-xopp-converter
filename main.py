import argparse
from xopp2rm import XOPP_TO_ZIP

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Xournal++ to reMarkable ZIP")
    parser.add_argument("input", help="Path to .xopp file")
    parser.add_argument("-o", "--output", default="converted.zip", help="Output ZIP path")
    
    args = parser.parse_args()
    XOPP_TO_ZIP(args.input, args.output)
