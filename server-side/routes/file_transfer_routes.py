"""
File Transfer Routes - Complete file transfer functionality
This file contains both phone-to-PC uploads and PC-to-phone downloads
Add this file as: server-side/routes/file_transfer_routes.py
"""

import os
import json
import shutil
import mimetypes
import base64
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create both blueprints
transfer_bp = Blueprint('transfer', __name__)
pc_transfer_bp = Blueprint('pc_transfer', __name__)

# Configuration
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'heic', 'raw',
    'mp3', 'mp4', 'avi', 'mov', 'wav', 'flac', 'm4a', 'mkv', 'wmv',
    'zip', 'rar', '7z', 'tar', 'gz', 'bz2',
    'json', 'xml', 'csv', 'log', 'py', 'js', 'html', 'css', 'md'
}

MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500MB
DEFAULT_UPLOAD_DIR = str(Path.home() / "Downloads" / "PhoneUploads")

def ensure_upload_directory(directory=None):
    """Ensure upload directory exists"""
    if directory is None:
        directory = DEFAULT_UPLOAD_DIR
    
    Path(directory).mkdir(parents=True, exist_ok=True)
    return directory

def is_allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_disk_space(path):
    """Get disk space information for a given path"""
    try:
        stats = shutil.disk_usage(path)
        total = stats.total
        used = stats.total - stats.free
        free = stats.free
        
        return {
            'total': total,
            'used': used,
            'free': free,
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'free_gb': round(free / (1024**3), 2),
            'usage_percent': round((used / total) * 100, 2)
        }
    except Exception as e:
        logger.error(f"Error getting disk space: {e}")
        return None

@transfer_bp.route('/file-transfer/status', methods=['GET'])
def get_transfer_status():
    """Get file transfer server status and capabilities"""
    try:
        return jsonify({
            "status": "active",
            "version": "2.0-enhanced",
            "features": [
                "upload", "download", "directory_management", 
                "disk_space", "file_validation"
            ],
            "allowedExtensions": list(ALLOWED_EXTENSIONS),
            "defaultDirectory": DEFAULT_UPLOAD_DIR,
            "maxFileSize": f"{MAX_FILE_SIZE_BYTES // (1024*1024)}MB",
            "supportedOperations": [
                "upload_files", "get_directories", "create_directory", "get_disk_space"
            ]
        })
    except Exception as e:
        logger.error(f"Error getting transfer status: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ==============================================================================
# PC-to-Phone Transfer Routes (Downloads)
# ==============================================================================

# Configuration for downloads
ALLOWED_DOWNLOAD_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp',
    'mp3', 'mp4', 'avi', 'mov', 'wav', 'flac',
    'zip', 'rar', '7z', 'tar', 'gz',
    'json', 'xml', 'csv', 'log'
}

MAX_DOWNLOAD_FILE_SIZE_MB = 100  # Limit file size for mobile downloads
MAX_FILES_PER_REQUEST = 10

def is_safe_path(base_path, path):
    """Check if path is safe (prevents directory traversal)"""
    try:
        base_path = Path(base_path).resolve()
        file_path = Path(base_path / path).resolve()
        return str(file_path).startswith(str(base_path))
    except (OSError, ValueError):
        return False

def get_file_size_mb(file_path):
    """Get file size in MB"""
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except OSError:
        return 0

def format_file_size(size_bytes):
    """Format file size for display"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

@pc_transfer_bp.route('/pc-transfer/browse', methods=['GET'])
def browse_directories():
    """Browse PC directories for file selection"""
    try:
        path = request.args.get('path', '')
        
        # Default to user's home directory if no path provided
        if not path:
            path = str(Path.home())
        
        # Security check
        base_path = Path.home()
        if not is_safe_path(base_path, path):
            return jsonify({
                "status": "error",
                "error": "Access denied to this path"
            }), 403
        
        target_path = Path(path)
        
        if not target_path.exists():
            return jsonify({
                "status": "error",
                "error": "Path does not exist"
            }), 404
        
        if not target_path.is_dir():
            return jsonify({
                "status": "error", 
                "error": "Path is not a directory"
            }), 400
        
        directories = []
        files = []
        
        try:
            for item in target_path.iterdir():
                try:
                    if item.is_dir():
                        directories.append({
                            "name": item.name,
                            "path": str(item),
                            "type": "directory",
                            "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                        })
                    elif item.is_file():
                        file_stat = item.stat()
                        file_ext = item.suffix.lower().lstrip('.')
                        
                        files.append({
                            "name": item.name,
                            "path": str(item),
                            "type": "file",
                            "size": file_stat.st_size,
                            "sizeFormatted": format_file_size(file_stat.st_size),
                            "extension": file_ext,
                            "downloadable": file_ext in ALLOWED_DOWNLOAD_EXTENSIONS and get_file_size_mb(item) <= MAX_DOWNLOAD_FILE_SIZE_MB,
                            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            "mimeType": mimetypes.guess_type(str(item))[0] or 'application/octet-stream'
                        })
                except (OSError, PermissionError):
                    continue  # Skip inaccessible files
                    
        except PermissionError:
            return jsonify({
                "status": "error",
                "error": "Permission denied to read directory"
            }), 403
        
        # Sort directories first, then files
        directories.sort(key=lambda x: x['name'].lower())
        files.sort(key=lambda x: x['name'].lower())
        
        return jsonify({
            "status": "success",
            "currentPath": str(target_path),
            "parentPath": str(target_path.parent) if target_path != target_path.parent else None,
            "directories": directories,
            "files": files,
            "totalDirectories": len(directories),
            "totalFiles": len(files)
        })
        
    except Exception as e:
        logger.error(f"Error browsing directories: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@pc_transfer_bp.route('/pc-transfer/file-info', methods=['POST'])
def get_file_info():
    """Get detailed information about selected files"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "error": "No JSON data provided"}), 400
        
        file_paths = data.get('paths', [])
        if not file_paths:
            return jsonify({"status": "error", "error": "No file paths provided"}), 400
        
        if len(file_paths) > MAX_FILES_PER_REQUEST:
            return jsonify({
                "status": "error", 
                "error": f"Too many files selected. Maximum {MAX_FILES_PER_REQUEST} files allowed"
            }), 400
        
        file_info_list = []
        total_size = 0
        downloadable_count = 0
        
        for file_path in file_paths:
            try:
                # Security check
                if not is_safe_path(Path.home(), file_path):
                    continue
                
                path = Path(file_path)
                if not path.exists() or not path.is_file():
                    continue
                
                file_stat = path.stat()
                file_size = file_stat.st_size
                file_ext = path.suffix.lower().lstrip('.')
                size_mb = get_file_size_mb(path)
                
                is_downloadable = (
                    file_ext in ALLOWED_DOWNLOAD_EXTENSIONS and 
                    size_mb <= MAX_DOWNLOAD_FILE_SIZE_MB
                )
                
                file_info = {
                    "path": str(path),
                    "name": path.name,
                    "type": "file",
                    "size": file_size,
                    "sizeFormatted": format_file_size(file_size),
                    "sizeMb": round(size_mb, 2),
                    "extension": file_ext,
                    "downloadable": is_downloadable,
                    "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "mimeType": mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
                }
                
                if not is_downloadable:
                    if file_ext not in ALLOWED_DOWNLOAD_EXTENSIONS:
                        file_info["skipReason"] = f"File type '.{file_ext}' not allowed"
                    elif size_mb > MAX_DOWNLOAD_FILE_SIZE_MB:
                        file_info["skipReason"] = f"File too large ({size_mb:.1f}MB > {MAX_DOWNLOAD_FILE_SIZE_MB}MB)"
                else:
                    downloadable_count += 1
                    total_size += file_size
                
                file_info_list.append(file_info)
                
            except (OSError, PermissionError) as e:
                logger.warning(f"Cannot access file {file_path}: {e}")
                continue
        
        return jsonify({
            "status": "success",
            "files": file_info_list,
            "summary": {
                "totalFiles": len(file_info_list),
                "downloadableFiles": downloadable_count,
                "totalSize": total_size,
                "totalSizeFormatted": format_file_size(total_size),
                "maxFileSizeMb": MAX_DOWNLOAD_FILE_SIZE_MB,
                "allowedExtensions": list(ALLOWED_DOWNLOAD_EXTENSIONS)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@pc_transfer_bp.route('/pc-transfer/download', methods=['POST'])
def download_files():
    """Download files to phone - returns download URLs"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "error": "No JSON data provided"}), 400
        
        file_paths = data.get('paths', [])
        if not file_paths:
            return jsonify({"status": "error", "error": "No file paths provided"}), 400
        
        download_info = []
        
        for file_path in file_paths:
            try:
                # Security check
                if not is_safe_path(Path.home(), file_path):
                    download_info.append({
                        "path": file_path,
                        "status": "error",
                        "error": "Access denied"
                    })
                    continue
                
                path = Path(file_path)
                if not path.exists() or not path.is_file():
                    download_info.append({
                        "path": file_path,
                        "status": "error", 
                        "error": "File not found"
                    })
                    continue
                
                file_ext = path.suffix.lower().lstrip('.')
                size_mb = get_file_size_mb(path)
                
                if file_ext not in ALLOWED_DOWNLOAD_EXTENSIONS:
                    download_info.append({
                        "path": file_path,
                        "status": "error",
                        "error": f"File type '.{file_ext}' not allowed"
                    })
                    continue
                
                if size_mb > MAX_DOWNLOAD_FILE_SIZE_MB:
                    download_info.append({
                        "path": file_path,
                        "status": "error",
                        "error": f"File too large ({size_mb:.1f}MB > {MAX_DOWNLOAD_FILE_SIZE_MB}MB)"
                    })
                    continue
                
                # Generate download URL
                encoded_path = base64.urlsafe_b64encode(file_path.encode()).decode()
                download_url = f"/pc-transfer/download-file/{encoded_path}"
                
                download_info.append({
                    "path": file_path,
                    "name": path.name,
                    "status": "ready",
                    "download_url": download_url,
                    "size": path.stat().st_size,
                    "size_formatted": format_file_size(path.stat().st_size),
                    "mime_type": mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
                })
                
            except Exception as e:
                logger.error(f"Error preparing download for {file_path}: {e}")
                download_info.append({
                    "path": file_path,
                    "status": "error",
                    "error": str(e)
                })
        
        successful_downloads = [d for d in download_info if d.get("status") == "ready"]
        
        return jsonify({
            "status": "success" if successful_downloads else "partial",
            "downloads": download_info,
            "summary": {
                "total_requested": len(file_paths),
                "ready_for_download": len(successful_downloads),
                "errors": len(download_info) - len(successful_downloads)
            }
        })
        
    except Exception as e:
        logger.error(f"Error preparing downloads: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@pc_transfer_bp.route('/pc-transfer/download-file/<encoded_path>', methods=['GET'])
def download_file(encoded_path):
    """Download a single file"""
    try:
        # Decode the file path
        try:
            file_path = base64.urlsafe_b64decode(encoded_path.encode()).decode()
        except Exception:
            return jsonify({"error": "Invalid file path"}), 400
        
        # Security check
        if not is_safe_path(Path.home(), file_path):
            return jsonify({"error": "Access denied"}), 403
        
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return jsonify({"error": "File not found"}), 404
        
        # Check file type and size
        file_ext = path.suffix.lower().lstrip('.')
        if file_ext not in ALLOWED_DOWNLOAD_EXTENSIONS:
            return jsonify({"error": "File type not allowed"}), 403
        
        if get_file_size_mb(path) > MAX_DOWNLOAD_FILE_SIZE_MB:
            return jsonify({"error": "File too large"}), 413
        
        # Get MIME type
        mime_type = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        
        # Send file
        return send_file(
            str(path),
            as_attachment=True,
            download_name=path.name,
            mimetype=mime_type
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({"error": str(e)}), 500

@pc_transfer_bp.route('/pc-transfer/quick-access', methods=['GET'])
def get_quick_access_folders():
    """Get commonly used folders for quick access"""
    try:
        home = Path.home()
        quick_folders = []
        
        # Common folders
        common_paths = [
            ("Home", home),
            ("Desktop", home / "Desktop"),
            ("Documents", home / "Documents"), 
            ("Downloads", home / "Downloads"),
            ("Pictures", home / "Pictures"),
            ("Videos", home / "Videos"),
            ("Music", home / "Music"),
        ]
        
        for name, path in common_paths:
            if path.exists() and path.is_dir():
                try:
                    # Count files in directory
                    file_count = sum(1 for item in path.iterdir() if item.is_file())
                    dir_count = sum(1 for item in path.iterdir() if item.is_dir())
                    
                    quick_folders.append({
                        "name": name,
                        "path": str(path),
                        "file_count": file_count,
                        "dir_count": dir_count,
                        "accessible": True
                    })
                except PermissionError:
                    quick_folders.append({
                        "name": name,
                        "path": str(path),
                        "file_count": 0,
                        "dir_count": 0,
                        "accessible": False
                    })
        
        return jsonify({
            "status": "success",
            "folders": quick_folders,
            "home_path": str(home)
        })
        
    except Exception as e:
        logger.error(f"Error getting quick access folders: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@transfer_bp.route('/file-transfer/directories', methods=['GET'])
def get_directories():
    """Get available upload directories"""
    try:
        home_dir = Path.home()
        directories = []
        
        # Common directories
        common_dirs = [
            ("Downloads", home_dir / "Downloads"),
            ("Documents", home_dir / "Documents"),
            ("Pictures", home_dir / "Pictures"),
            ("Videos", home_dir / "Videos"),
            ("Music", home_dir / "Music"),
            ("Desktop", home_dir / "Desktop"),
        ]
        
        # Add phone uploads directory
        phone_uploads_dir = Path(DEFAULT_UPLOAD_DIR)
        ensure_upload_directory()
        directories.append({
            "name": "Phone Uploads",
            "path": str(phone_uploads_dir),
            "exists": phone_uploads_dir.exists(),
            "writable": True
        })
        
        # Add common directories if they exist
        for name, path in common_dirs:
            if path.exists() and path.is_dir():
                try:
                    # Test if writable
                    test_file = path / ".write_test"
                    test_file.touch()
                    test_file.unlink()
                    writable = True
                except (PermissionError, OSError):
                    writable = False
                
                directories.append({
                    "name": name,
                    "path": str(path),
                    "exists": True,
                    "writable": writable
                })
        
        return jsonify({
            "status": "success",
            "directories": directories,
            "homeDirectory": str(home_dir)
        })
        
    except Exception as e:
        logger.error(f"Error getting directories: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "directories": [],
            "homeDirectory": str(Path.home())
        }), 500

@transfer_bp.route('/file-transfer/upload', methods=['POST'])
def upload_files():
    """Handle file uploads from phone"""
    try:
        if 'files' not in request.files:
            return jsonify({
                "status": "error",
                "error": "No files provided"
            }), 400
        
        files = request.files.getlist('files')
        target_directory = request.form.get('target_directory', DEFAULT_UPLOAD_DIR)
        
        # Ensure target directory exists
        target_path = Path(target_directory)
        ensure_upload_directory(target_directory)
        
        uploaded_files = []
        skipped_files = []
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
                
            try:
                if not is_allowed_file(file.filename):
                    skipped_files.append({
                        "filename": file.filename,
                        "reason": "File type not allowed"
                    })
                    continue
                
                # Secure the filename
                filename = secure_filename(file.filename)
                if not filename:
                    filename = f"uploaded_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Handle duplicate filenames
                file_path = target_path / filename
                counter = 1
                original_stem = file_path.stem
                original_suffix = file_path.suffix
                
                while file_path.exists():
                    new_name = f"{original_stem}_{counter}{original_suffix}"
                    file_path = target_path / new_name
                    counter += 1
                
                # Save the file
                file.save(str(file_path))
                file_size = file_path.stat().st_size
                
                uploaded_files.append({
                    "originalName": file.filename,
                    "savedName": file_path.name,
                    "path": str(file_path),
                    "size": file_size
                })
                
                logger.info(f"Uploaded file: {file_path.name} ({file_size} bytes)")
                
            except Exception as e:
                logger.error(f"Error uploading file {file.filename}: {e}")
                errors.append(f"Error uploading {file.filename}: {str(e)}")
        
        response_data = {
            "status": "success" if uploaded_files else "partial" if skipped_files else "error",
            "uploadedFiles": uploaded_files,
            "skippedFiles": skipped_files,
            "targetDirectory": target_directory,
            "totalUploaded": len(uploaded_files),
            "totalSkipped": len(skipped_files)
        }
        
        if errors:
            response_data["errors"] = errors
        
        if uploaded_files:
            response_data["message"] = f"Successfully uploaded {len(uploaded_files)} files"
        elif skipped_files:
            response_data["message"] = f"All {len(skipped_files)} files were skipped"
        else:
            response_data["message"] = "No files were uploaded"
            response_data["status"] = "error"
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in file upload: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@transfer_bp.route('/file-transfer/create-directory', methods=['POST'])
def create_directory():
    """Create a new directory for uploads"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "No JSON data provided"
            }), 400
        
        action = data.get('action')
        if action != 'create_directory':
            return jsonify({
                "status": "error",
                "error": "Invalid action"
            }), 400
        
        directory_data = data.get('data', {})
        path = directory_data.get('path')
        
        if not path:
            return jsonify({
                "status": "error",
                "error": "No path provided"
            }), 400
        
        # Security check - ensure path is within allowed locations
        target_path = Path(path)
        home_path = Path.home()
        
        try:
            target_path.resolve().relative_to(home_path.resolve())
        except ValueError:
            return jsonify({
                "status": "error",
                "error": "Directory must be within user home directory"
            }), 403
        
        # Create directory
        target_path.mkdir(parents=True, exist_ok=True)
        
        return jsonify({
            "status": "success",
            "message": f"Directory created: {path}"
        })
        
    except Exception as e:
        logger.error(f"Error creating directory: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@transfer_bp.route('/file-transfer/disk-space', methods=['GET'])
def get_disk_space_info():
    """Get disk space information for a directory"""
    try:
        directory = request.args.get('directory', DEFAULT_UPLOAD_DIR)
        
        # Ensure directory exists
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path = Path(DEFAULT_UPLOAD_DIR)
            ensure_upload_directory()
        
        space_info = get_disk_space(str(dir_path))
        
        if space_info is None:
            return jsonify({
                "status": "error",
                "error": "Could not get disk space information"
            }), 500
        
        return jsonify({
            "status": "success",
            "directory": str(dir_path),
            **space_info
        })
        
    except Exception as e:
        logger.error(f"Error getting disk space: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500
