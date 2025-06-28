# Git Pocket - GitHub Actions

A powerful "Read It Later" tool that saves web articles to your own GitHub Pages site using GitHub Actions. Your personal reading archive powered by GitHub with advanced features like search, RSS feeds, and image handling.

[Demo](https://smoqadam.github.io/git-pocket/index.html)

## ✨ Features

- **📚 Article Extraction**: Clean article text with metadata (author, date)
- **🔍 Full-Text Search**: JavaScript-powered search through titles and authors
- **📱 Responsive Design**: Beautiful, mobile-friendly interface
- **🖼️ Image Handling**: Downloads and optimizes images for offline viewing
- **📡 RSS Feed**: Auto-generated RSS feed for your saved articles
- **🔄 Duplicate Detection**: Prevents saving the same article twice
- **📊 Rich Metadata**: Extracts and displays author and date
- **🎨 Modern UI**: Clean, professional design with hover effects and animations
- **📖 Reading Experience**: Optimized typography and layout for comfortable reading

## Why This Exists

GitHub is free and many developers already use it. This project turns your GitHub account into a personal read-it-later service with advanced features. No subscriptions, no third-party storage, just your own archive built with tools you already have.

## How It Works

The system uses GitHub's repository dispatch feature to trigger article extraction:

1. **You send a URL** via HTTP POST request to GitHub's API
2. **GitHub Actions triggers** and checks out your repository
3. **Article extraction** happens using Python's newspaper library
4. **Metadata is extracted** (author, date)
5. **Images are downloaded** and optimized for local storage
6. **Content is saved** as a formatted HTML file with rich styling
7. **Search index is updated** with article metadata
8. **RSS feed is generated** with latest articles
9. **GitHub Pages deploys** the updated site automatically

```
URL Request → GitHub API → Actions Workflow → Extract Article → Process Images → Update Search Index → Generate RSS → Deploy
```

## Setup Instructions

### 1. Fork this repository

### 2. Enable GitHub Pages

1. Go to your repository's **Settings** tab
2. Scroll down to **Pages** section
3. Set **Source** to "Deploy from a branch"
4. Select **gh-pages** branch and **/ (root)** folder
5. Click **Save**

### 3. Generate a Personal Access Token

1. Go to GitHub **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Give it a descriptive name like "ReadItLater Dispatch"
4. Select these scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
5. Copy the generated token (you won't see it again!)

### 4. Test the Setup

Send a test request to add your first article:

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_PERSONAL_ACCESS_TOKEN" \
  https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO_NAME/dispatches \
  -d '{"event_type":"new-url","client_payload":{"url":"https://example.com/some-article"}}'
```

Replace:
- `YOUR_PERSONAL_ACCESS_TOKEN` with your token
- `YOUR_USERNAME` with your GitHub username
- `YOUR_REPO_NAME` with your repository name
- The URL with an actual article you want to save

## Usage

### Adding Articles

#### Method 1: Command Line (cURL)

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/dispatches \
  -d '{"event_type":"new-url","client_payload":{"url":"ARTICLE_URL"}}'
```

#### Method 2: Browser Bookmarklet

Create a bookmarklet for one-click saving. Add this as a bookmark:

```javascript
javascript:(function(){var url=encodeURIComponent(window.location.href);fetch('https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/dispatches',{method:'POST',headers:{'Accept':'application/vnd.github.v3+json','Authorization':'token YOUR_TOKEN','Content-Type':'application/json'},body:JSON.stringify({event_type:'new-url',client_payload:{url:window.location.href}})}).then(r=>r.ok?alert('Article saved!'):alert('Error saving article'));})();
```

## Contributing

Feel free to submit issues and enhancement requests! Some ideas for improvements:

## License

This project is open source and available under the [MIT License](LICENSE).
