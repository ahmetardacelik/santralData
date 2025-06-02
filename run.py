#!/usr/bin/env python3
"""
EPIAS Elektrik Verisi Çekici - Ana Başlangıç Scripti
"""

import os
import sys
import argparse
from pathlib import Path

def setup_environment():
    """Environment setup"""
    # Add backend directory to Python path
    backend_dir = Path(__file__).parent / 'backend'
    sys.path.insert(0, str(backend_dir))
    
    # Create necessary directories
    directories = [
        'backend/logs',
        'backend/downloads',
        'data/logs',
        'data/downloads'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory created/verified: {directory}")

def run_development():
    """Run in development mode"""
    print("🚀 Starting EPIAS App in DEVELOPMENT mode...")
    setup_environment()
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Import and run Flask app
    from backend.app import app, create_app
    
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    
    print(f"🌐 Web Interface: http://localhost:{port}/")
    print(f"📚 API Docs: http://localhost:{port}/api")
    print(f"❤️ Health Check: http://localhost:{port}/api/health")
    print("🔄 Auto-reload enabled")
    print("-" * 50)
    
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=True,
        use_reloader=True
    )

def run_production():
    """Run in production mode"""
    print("🚀 Starting EPIAS App in PRODUCTION mode...")
    setup_environment()
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        import gunicorn
        print("🔄 Using Gunicorn WSGI server...")
        
        # Run with Gunicorn
        port = int(os.getenv('PORT', 5000))
        workers = int(os.getenv('WORKERS', 2))
        
        cmd = [
            'gunicorn',
            '--bind', f'0.0.0.0:{port}',
            '--workers', str(workers),
            '--timeout', '300',
            '--keep-alive', '2',
            '--worker-class', 'sync',
            '--worker-connections', '1000',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            '--access-logfile', 'backend/logs/access.log',
            '--error-logfile', 'backend/logs/error.log',
            '--log-level', 'info',
            'backend.app:app'
        ]
        
        print(f"🌐 Production server: http://0.0.0.0:{port}/")
        print(f"👥 Workers: {workers}")
        print("-" * 50)
        
        os.execvp('gunicorn', cmd)
        
    except ImportError:
        print("⚠️ Gunicorn not found, falling back to Flask dev server...")
        from backend.app import app, create_app
        
        app = create_app()
        port = int(os.getenv('PORT', 5000))
        
        app.run(
            host='0.0.0.0', 
            port=port, 
            debug=False
        )

def run_docker():
    """Run with Docker"""
    print("🐳 Starting EPIAS App with Docker...")
    
    try:
        import subprocess
        
        # Check if Docker is available
        subprocess.run(['docker', '--version'], check=True, capture_output=True)
        
        print("🔨 Building Docker image...")
        subprocess.run(['docker', 'build', '-t', 'epias-app', '.'], check=True)
        
        print("🚀 Starting container...")
        port = int(os.getenv('PORT', 5000))
        
        cmd = [
            'docker', 'run',
            '--rm',
            '-p', f'{port}:5000',
            '-v', f'{Path.cwd()}/data:/app/data',
            '--name', 'epias-app',
            'epias-app'
        ]
        
        print(f"🌐 Docker server: http://localhost:{port}/")
        print("-" * 50)
        
        subprocess.run(cmd)
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not available. Please install Docker or use Python mode.")
        sys.exit(1)

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask',
        'requests',
        'pandas',
        'openpyxl'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        print("\n   Or install all requirements:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ All dependencies satisfied")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='EPIAS Elektrik Verisi Çekici')
    parser.add_argument(
        'mode', 
        choices=['dev', 'prod', 'docker'], 
        help='Run mode: dev (development), prod (production), docker'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=5000, 
        help='Port to run on (default: 5000)'
    )
    parser.add_argument(
        '--skip-deps', 
        action='store_true', 
        help='Skip dependency check'
    )
    
    args = parser.parse_args()
    
    # Set port environment variable
    os.environ['PORT'] = str(args.port)
    
    print("⚡ EPIAS Elektrik Verisi Çekici")
    print("=" * 50)
    
    # Check dependencies (unless skipped)
    if not args.skip_deps and args.mode != 'docker':
        check_dependencies()
    
    # Run in selected mode
    if args.mode == 'dev':
        run_development()
    elif args.mode == 'prod':
        run_production()
    elif args.mode == 'docker':
        run_docker()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1) 