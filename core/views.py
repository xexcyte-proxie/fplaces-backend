import os
from django.conf import settings
from django.http import Http404, HttpResponse

def guide_view(request):
    guide_path = os.path.join(settings.BASE_DIR, "doc", "frontend_integration_guide.html")
    if not os.path.exists(guide_path):
        raise Http404("Guide not found")
    with open(guide_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HttpResponse(content)


def root_view(request):
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>fPlaces is Live</title>
    <link rel="icon" href="data:,">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #08090c;
            --card-bg: rgba(20, 24, 33, 0.6);
            --border-color: rgba(255, 255, 255, 0.08);
            --primary-glow: rgba(0, 224, 150, 0.15);
            --accent-color: #00e096;
            --text-main: #ffffff;
            --text-muted: #8b949e;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
        }

        /* Abstract glowing background circles */
        .ambient-glow {
            position: absolute;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(0, 224, 150, 0.12) 0%, rgba(0,0,0,0) 70%);
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 1;
            pointer-events: none;
            filter: blur(40px);
        }

        .container {
            position: relative;
            z-index: 2;
            width: 90%;
            max-width: 440px;
            text-align: center;
            animation: fadeIn 1s ease-out;
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 40px 30px;
            border-radius: 24px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), 
                        0 0 50px var(--primary-glow);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 25px 45px rgba(0, 0, 0, 0.6), 
                        0 0 60px rgba(0, 224, 150, 0.25);
            border-color: rgba(0, 224, 150, 0.3);
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 224, 150, 0.1);
            border: 1px solid rgba(0, 224, 150, 0.2);
            padding: 8px 16px;
            border-radius: 100px;
            color: var(--accent-color);
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 24px;
            text-transform: uppercase;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--accent-color);
            border-radius: 50%;
            position: relative;
            box-shadow: 0 0 10px var(--accent-color);
        }

        .status-dot::after {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            background-color: var(--accent-color);
            border-radius: 50%;
            animation: pulse 1.8s infinite ease-in-out;
        }

        h1 {
            font-size: 38px;
            font-weight: 800;
            line-height: 1.2;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #ffffff 40%, #00e096 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        p {
            font-size: 16px;
            color: var(--text-muted);
            line-height: 1.5;
        }

        @keyframes pulse {
            0% {
                transform: scale(1);
                opacity: 1;
            }
            100% {
                transform: scale(3.5);
                opacity: 0;
            }
        }

        .button-group {
            display: flex;
            gap: 16px;
            margin-top: 32px;
            justify-content: center;
        }

        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: var(--accent-color);
            color: var(--bg-color);
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .btn:hover {
            transform: scale(1.05);
            box-shadow: 0 0 20px rgba(0, 224, 150, 0.4);
        }

        .btn-outline {
            background: transparent;
            color: var(--accent-color);
            border: 1px solid var(--accent-color);
        }

        .btn-outline:hover {
            background: rgba(0, 224, 150, 0.1);
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
</head>
<body>
    <div class="ambient-glow"></div>
    <div class="container">
        <div class="card">
            <div class="status-badge">
                <span class="status-dot"></span>
                System Status
            </div>
            <h1>fPlaces is live</h1>
            <p>The real-time, venue-scoped social platform API and engine are running smoothly.</p>
            <div class="button-group">
                <a href="/api/docs/" class="btn">Swagger Docs</a>
                <a href="/api/redoc/" class="btn btn-outline">ReDoc</a>
                <a href="/api/guide.html" class="btn btn-outline" style="border-color: #8b949e; color: #8b949e;">Integration Guide</a>
            </div>
        </div>
    </div>
</body>
</html>"""
    return HttpResponse(html_content)
