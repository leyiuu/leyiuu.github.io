# leyiuu.github.io
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>個人主頁</title>
  <style>
    body {
      margin: 0;
      font-family: "Segoe UI", sans-serif;
      background-color: #f4f4f4;
    }

    .top-section {
      display: flex;
      height: 33vh;
      background-color: #ffffff;
      padding: 2rem;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    .photo-container {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .photo-container img {
      height: 100%;
      max-height: 100%;
      width: auto;
      border-radius: 8px;
      object-fit: cover;
    }

    .info-container {
      flex: 2;
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding-left: 2rem;
    }

    .info-container h1 {
      font-size: 2rem;
      margin: 0;
      color: #333;
    }

    .info-container p {
      margin: 0.3rem 0;
      color: #666;
      font-size: 1rem;
    }
  </style>
</head>
<body>
  <section class="top-section">
    <div class="photo-container">
      <img src="P1000058.JPG" alt="個人照片" />
    </div>
    <div class="info-container">
      <h1>你的名字</h1>
      <p><strong>職位：</strong>前端工程師</p>
      <p><strong>目前工作：</strong>在 ABC 公司擔任開發工程師</p>
      <p><strong>學習方向：</strong>React、TypeScript、AI 工具整合</p>
      <p><strong>已有經歷：</strong>3 年網站開發經驗、2 個產品上線</p>
      <p><strong>聯絡方式：</strong>you@example.com</p>
    </div>
  </section>
</body>
</html>
