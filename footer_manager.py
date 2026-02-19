"""Footer image management"""
from pathlib import Path

# Footer image paths
FOOTER_IMAGES = {
    'benefits': Path(__file__).parent / 'assets' / 'footer' / 'benefits.png',
    'insurance_comparison': Path(__file__).parent / 'assets' / 'footer' / 'insurance_comparison.png',
    'benefits_combined': Path(__file__).parent / 'assets' / 'footer' / 'benefits_combined.png',
}


def get_footer_images() -> list[Path]:
    """
    Get list of footer images to append to blog post
    
    Returns:
        list[Path]: Footer image paths
    """
    return [
        FOOTER_IMAGES['benefits'],
        FOOTER_IMAGES['insurance_comparison']
    ]


def get_combined_footer_image() -> Path:
    """
    Get combined footer image (alternative layout)
    
    Returns:
        Path: Combined footer image path
    """
    return FOOTER_IMAGES['benefits_combined']
