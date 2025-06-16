# Read It Later - GitHub Actions

A serverless "Read It Later" service that automatically extracts and saves web articles to a GitHub Pages site using GitHub Actions. Perfect for creating your own personal reading archive without any hosting costs.

## Why This Exists

In our information-rich world, we constantly come across interesting articles but don't always have time to read them immediately. Traditional read-later services are great, but they:

- Store your data on third-party servers
- Often require subscriptions for advanced features
- May disappear or change their terms of service
- Don't give you full control over your reading archive

This project solves these problems by:

- **Using GitHub as your backend** - Your articles are stored in your own repository
- **Zero hosting costs** - Leverages GitHub Pages for free hosting
- **Complete ownership** - All your data stays in your GitHub account
- **Automatic archiving** - Articles are extracted and formatted for offline reading
- **Simple interface** - Clean, readable HTML pages with navigation

## How It Works

The system uses GitHub's repository dispatch feature to trigger article extraction:

1. **You send a URL** via HTTP POST request to GitHub's API
2. **GitHub Actions triggers** and checks out your repository
3. **Article extraction** happens using Python's newspaper library
4. **Content is saved** as a formatted HTML file in the `/entries` directory
5. **Index is updated** with a link to the new article
6. **GitHub Pages deploys** the updated site automatically

```
URL Request → GitHub API → Actions Workflow → Extract Article → Update Site → Deploy
```

## Setup Instructions

### 1. Fork or Clone This Repository

```bash
git clone https://github.com/yourusername/ReadItLater-GA.git
cd ReadItLater-GA
```

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

#### Method 3: Mobile Shortcut (iOS)

Create an iOS Shortcut that:
1. Gets the current webpage URL
2. Makes the HTTP request to GitHub API
3. Shows a confirmation message

### Viewing Your Archive

Once articles are processed, visit your GitHub Pages URL:
`https://YOUR_USERNAME.github.io/YOUR_REPO_NAME`

## Project Structure

```
ReadItLater-GA/
├── .github/workflows/
│   └── publish.yaml          # GitHub Actions workflow
├── entries/                  # Generated article files (created automatically)
├── extract.py               # Main extraction script
├── requirements.txt         # Python dependencies
├── index.html              # Generated index page (created automatically)
└── README.md               # This file
```

## Customization

### Styling

Edit the CSS in `extract.py` within the `html_content` strings to customize:
- Colors and fonts
- Layout and spacing
- Mobile responsiveness

### Article Processing

Modify `extract.py` to:
- Change filename format
- Add metadata extraction
- Include article images
- Filter content

### Workflow Triggers

Edit `.github/workflows/publish.yaml` to:
- Change trigger conditions
- Add notifications
- Modify deployment settings

## Limitations

- **Article quality depends on the source** - Some sites may not extract cleanly
- **JavaScript-heavy sites** may not work well with the newspaper library
- **Rate limits** - GitHub API has rate limits (5000 requests/hour for authenticated users)
- **Repository size** - Large numbers of articles may impact repository size

## Troubleshooting

### Articles aren't being saved
1. Check the Actions tab for workflow errors
2. Verify your personal access token has correct permissions
3. Ensure the repository dispatch payload is correctly formatted

### Extraction fails for certain sites
- Some sites block automated access
- Try the URL in a private browser to ensure it's publicly accessible
- Check if the site requires JavaScript to load content

### GitHub Pages not updating
- Check if GitHub Pages is enabled in repository settings
- Verify the gh-pages branch exists and has content
- GitHub Pages updates may take a few minutes to propagate

## Contributing

Feel free to submit issues and enhancement requests! Some ideas for improvements:

- Better mobile interface
- Search functionality
- Tag/category system
- Export options
- Better error handling

## License

This project is open source and available under the [MIT License](LICENSE).

---

**Happy Reading!** 📚
