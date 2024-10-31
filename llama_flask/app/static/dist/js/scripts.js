// 當 DOM 完全加載後，初始化事件監聽器
document.addEventListener('DOMContentLoaded', function () {
    // 當表單提交時，觸發異步處理邏輯
    document.getElementById('prediction-form').onsubmit = async function (event) {
        event.preventDefault(); // 防止表單的默認提交行為，避免頁面重新加載

        // 顯示載入信息
        document.getElementById('loadingMessage').style.display = 'block'; // 顯示加載提示
        document.getElementById('result').innerHTML = '';  // 清除之前的結果
        document.getElementById('marquee').innerHTML = '正在分析中...';  // 設置跑馬燈的初始內容
        document.getElementById('marquee').classList.add('marquee-animation'); // 開始跑馬燈動畫

        // 獲取表單數據
        const formData = new FormData(this); 

        try {
            // 同時發送兩個 AJAX 請求，一個用於預測，一個用於獲取新聞數據
            const [predictResponse, newsResponse] = await Promise.all([
                fetch('/predict', { method: 'POST', body: formData }),  // 預測請求
                fetch('/news', { method: 'POST', body: formData })  // 新聞請求
            ]);

            // 處理預測響應
            if (predictResponse.ok) {
                const [sentiment_mean, result] = await predictResponse.json();  // 獲取預測結果
                document.getElementById('loadingMessage').style.display = 'none'; // 隱藏加載信息

                // 構建並顯示預測結果表格
                let table = '<table class="table table-bordered"><thead><tr><th>Title</th><th>Details</th></tr></thead><tbody>';
                table += `<tr><td colspan="2"><strong>Predictions</strong></td></tr>`;
                for (let key in result) {
                    table += `<tr><td>${key}</td><td>${result[key]}</td></tr>`;
                }
                table += '</tbody></table>';
                document.getElementById('dynamic-result').innerHTML = table; // 顯示預測結果

                // 構建並顯示 sentiment_mean 數據表格
                let sentimentTable = '<table class="table table-bordered"><thead><tr><th>Field</th><th>Value</th></tr></thead><tbody>';
                sentimentTable += `<tr><td colspan="2"><strong>Sentiment Mean</strong></td></tr>`;
                for (let stockID in sentiment_mean) {
                    let stockData = sentiment_mean[stockID];
                    for (let dateStr in stockData) {
                        let data = stockData[dateStr];
                        sentimentTable += `<tr><td>Stock ID</td><td>${stockID}</td></tr>`;
                        sentimentTable += `<tr><td>Date</td><td>${data['date']}</td></tr>`;
                        sentimentTable += `<tr><td>Arousal Mean</td><td>${data['arousal_mean']}</td></tr>`;
                        sentimentTable += `<tr><td>Count</td><td>${data['count']}</td></tr>`;
                    }
                }
                sentimentTable += '</tbody></table>';
                document.getElementById('dynamic-sentiment-mean').innerHTML = sentimentTable; // 顯示情緒數據
            } else {
                // 預測請求失敗，顯示錯誤信息
                document.getElementById('loadingMessage').innerHTML = 'Error: 無法取得預測結果';
            }

        // 處理新聞響應
        if (newsResponse.ok) {
            const newsData = await newsResponse.json();  // 獲取新聞數據
            let newsHtml = '';  // 初始化 HTML 字串

            // 動態生成新聞列表
            for (const [source, newsList] of Object.entries(newsData)) {
                newsHtml += `
                    <div class="news-source-section">
                        <h2 class="text-primary mb-3">${source}</h2>
                        <ul class="list-group mb-4">
                `;
                newsList.forEach(news => {
                    newsHtml += `
                        <li class="list-group-item">
                            <a href="${news.link}" target="_blank" class="text-dark text-decoration-none">${news.headline}</a>
                        </li>
                    `;
                });
                newsHtml += `</ul></div>`;
            }
            document.getElementById('news-results').innerHTML = newsHtml;  // 顯示新聞結果
        } else {
            console.error('找不到相關的新聞', newsResponse.statusText);
            document.getElementById('news-results').innerHTML = `
                <div class="alert alert-warning" role="alert">
                    找不到相關的新聞: ${newsResponse.statusText}
                </div>
            `;  // 顯示新聞錯誤信息
        }


            // 使用 SSE（Server-Sent Events）實時更新股票分析結果
            const eventSource = new EventSource('/sse_stock_analysis');
            eventSource.onmessage = function (event) {
                const marquee = document.getElementById('marquee');
                marquee.innerHTML = event.data;  // 更新跑馬燈的內容
                marquee.classList.add('marquee-animation');  // 確保跑馬燈動畫繼續

                // 當分析完成時，停止 SSE 並關閉跑馬燈動畫
                if (event.data === "分析完成!") {
                    eventSource.close();  // 關閉 SSE 連接
                    marquee.classList.remove('marquee-animation');  // 停止跑馬燈動畫
                    marquee.innerHTML = "分析完成!";  // 更新跑馬燈內容
                }
            };

        } catch (error) {
            // 捕獲異常並顯示錯誤信息
            console.error('Error:', error);
            document.getElementById('loadingMessage').innerHTML = 'Error: 無法連接到伺服器';
        }
    };
});
