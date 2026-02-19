"""Image optimization for blog publishing"""
from PIL import Image
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """Optimize images for web (size, quality, dimensions)"""
    
    def __init__(self, max_width: int = 1200, quality: int = 85):
        """
        Args:
            max_width: Maximum width in pixels (default: 1200px for blog)
            quality: JPEG quality 1-100 (default: 85 for good balance)
        """
        self.max_width = max_width
        self.quality = quality
    
    def optimize(self, image_path: Path, output_path: Path) -> dict:
        """
        Optimize a single image
        
        Returns:
            dict: {
                'original_size': bytes,
                'optimized_size': bytes,
                'reduction': percent,
                'dimensions': (width, height)
            }
        """
        try:
            # Get original size
            original_size = image_path.stat().st_size
            
            # Open image
            img = Image.open(image_path)
            original_dims = img.size
            
            # Convert to RGB if necessary (handle RGBA, grayscale, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large
            if img.width > self.max_width:
                ratio = self.max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((self.max_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"Resized {image_path.name}: {original_dims} → {img.size}")
            
            # Save optimized
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(
                output_path,
                'JPEG',
                quality=self.quality,
                optimize=True,  # Enable optimization
                progressive=True  # Progressive JPEG (better web loading)
            )
            
            # Get new size
            optimized_size = output_path.stat().st_size
            reduction = ((original_size - optimized_size) / original_size) * 100
            
            stats = {
                'original_size': original_size,
                'optimized_size': optimized_size,
                'reduction': round(reduction, 1),
                'dimensions': img.size,
                'original_dimensions': original_dims
            }
            
            logger.info(
                f"Optimized {image_path.name}: "
                f"{self._format_size(original_size)} → {self._format_size(optimized_size)} "
                f"({stats['reduction']}% reduction)"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Optimization failed for {image_path}: {e}")
            raise
    
    def batch_optimize(self, image_paths: list[Path], output_dir: Path) -> dict:
        """
        Optimize multiple images
        
        Returns:
            dict: {
                'images': [stats1, stats2, ...],
                'total_original': bytes,
                'total_optimized': bytes,
                'total_reduction': percent,
                'optimized_paths': [path1, path2, ...]
            }
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        optimized_paths = []
        total_original = 0
        total_optimized = 0
        
        for i, img_path in enumerate(image_paths):
            output_path = output_dir / f"optimized_{i+1:02d}.jpg"
            stats = self.optimize(img_path, output_path)
            
            results.append(stats)
            optimized_paths.append(output_path)
            total_original += stats['original_size']
            total_optimized += stats['optimized_size']
        
        total_reduction = ((total_original - total_optimized) / total_original) * 100
        
        summary = {
            'images': results,
            'count': len(results),
            'total_original': total_original,
            'total_optimized': total_optimized,
            'total_reduction': round(total_reduction, 1),
            'optimized_paths': optimized_paths,
            'avg_size': self._format_size(total_optimized // len(results)) if results else "0 KB"
        }
        
        logger.info(
            f"Batch optimization complete: {len(results)} images, "
            f"{self._format_size(total_original)} → {self._format_size(total_optimized)} "
            f"({summary['total_reduction']}% reduction)"
        )
        
        return summary
    
    @staticmethod
    def _format_size(bytes_size: int) -> str:
        """Format bytes to human-readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
