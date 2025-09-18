import os
from flask import Flask, session, request, redirect, render_template, url_for
from dotenv import load_dotenv
import spotipy

# .envファイルから環境変数を読み込む
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Spotipyが環境変数から設定を読み込む
# SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI

@app.route('/')
def index():
    """トップページ。ログイン状態に応じて表示を切り替える"""
    if 'token_info' not in session:
        return render_template('login.html')
    
    # トークンが期限切れでないか確認
    sp_oauth = create_spotify_oauth()
    token_info = session.get('token_info', None)
    if not token_info or sp_oauth.is_token_expired(token_info):
        return redirect(url_for('login'))
        
    return redirect(url_for('profile'))

@app.route('/login')
def login():
    """Spotifyの認証ページにリダイレクトする"""
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/logout')
def logout():
    """セッションをクリアしてログアウトする"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/callback')
def callback():
    """Spotifyからのコールバックを処理する"""
    sp_oauth = create_spotify_oauth()
    # URLから認可コードを取得
    code = request.args.get('code')
    # 認可コードを使ってアクセストークンを取得
    token_info = sp_oauth.get_access_token(code)
    # トークン情報をセッションに保存
    session['token_info'] = token_info
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    """ユーザーのプロフィールとトップトラックを表示する"""
    token_info = session.get('token_info', None)
    if not token_info:
        # セッションがなければログインページへ
        return redirect(url_for('index'))

    # トークンが期限切れの場合はリフレッシュ
    sp_oauth = create_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    
    # Spotify APIクライアントを作成
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    # ユーザー情報とトップトラックを取得
    user = sp.current_user()
    top_tracks = sp.current_user_top_tracks(limit=5, time_range='short_term')['items']
    
    return render_template('profile.html', user=user, top_tracks=top_tracks)

def create_spotify_oauth():
    """SpotifyOAuthオブジェクトを生成するヘルパー関数"""
    return spotipy.SpotifyOAuth(scope='user-top-read')

if __name__ == '__main__':
    app.run(debug=True)