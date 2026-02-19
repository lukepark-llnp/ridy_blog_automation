"""Image watermark processing"""
from PIL import Image
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Path to RIDY logo
LOGO_PATH = Path(__file__).parent / "assets" / "ridy_logo.png"


def add_watermark(image_path: str | Path, output_path: str | Path, logo_path: Path = LOGO_PATH) -> Path:
    """
    Add RIDY logo watermark to image (bottom-right corner)
    
    Args:
        image_path: Input image path
        output_path: Output image path
        logo_path: Path to watermark logo (default: assets/ridy_logo.png)
        
    Returns:
        Path to watermarked image
    """
    try:
        # Open image
        img = Image.open(image_path).convert('RGB')
        
        # Open logo
        if not logo_path.exists():
            logger.warning(f"Logo not found: {logo_path}, skipping watermark")
            # Just copy the image
            img.save(output_path, 'JPEG', quality=95)
            return Path(output_path)
        
        logo = Image.open(logo_path).convert('RGBA')
        
        # Calculate logo size (32% of image width - 4x bigger than previous 8%)
        logo_width = int(img.width * 0.32)
        logo_ratio = logo.height / logo.width
        logo_height = int(logo_width * logo_ratio)
        
        # Resize logo
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # Position: bottom-right with margin
        margin = int(img.width * 0.02)  # 2% margin
        x = img.width - logo_width - margin
        y = img.height - logo_height - margin
        
        # Create a new image with alpha channel for compositing
        img_rgba = img.convert('RGBA')
        
        # Paste logo directly (using alpha channel as mask)
        # 흰색 배경 없이 투명도 유지하여 합성
        img_rgba.paste(logo, (x, y), logo)
        
        # Convert back to RGB for JPEG
        final = img_rgba.convert('RGB')
        
        # Save
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        final.save(output_path, 'JPEG', quality=95)
        
        logger.info(f"Watermarked: {image_path} -> {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Watermark failed for {image_path}: {e}")
        raise


def batch_watermark(image_paths: list[Path], output_dir: Path) -> list[Path]:
    """
    Add watermark to multiple images
    
    Args:
        image_paths: List of input image paths
        output_dir: Output directory
        
    Returns:
        List of watermarked image paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    watermarked = []
    
    for i, img_path in enumerate(image_paths):
        output_path = output_dir / f"watermarked_{i+1:02d}.jpg"
        watermarked.append(add_watermark(img_path, output_path))
    
    return watermarked
