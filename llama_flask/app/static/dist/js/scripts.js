/*// 當 DOM 完全加載後，初始化事件監聽器
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
                const { sentiment_mean, result, chart_image_base64 } = await predictResponse.json();  // 獲取預測結果
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

                document.getElementById('dynamic-sentiment-mean').innerHTML = sentimentTable; // 顯示情緒數據

                // 顯示情緒趨勢圖（Base64 編碼的圖片）
                if (chart_image_base64) {
                    const imgElement = `<img src="data:image/png;base64,${chart_image_base64}" alt="情緒趨勢圖" style="width:100%; height:auto;" />`;
                    document.getElementById('dynamic-sentiment-chart-image').innerHTML = imgElement;
                } else {
                    document.getElementById('loadingMessage').innerHTML = 'Error: predict圖像生成失敗';
                }


            } else {
                // 預測請求失敗，顯示錯誤信息
                document.getElementById('loadingMessage').innerHTML = 'Error: predict無法取得預測結果';
            }

            // 處理新聞響應
            if (newsResponse.ok) {
                const newsData = await newsResponse.json();  // 獲取新聞數據
                let newsHtml = '';  // 初始化 HTML 字串

                // 動態生成新聞卡片
                for (const [source, newsList] of Object.entries(newsData)) {
                    newsHtml += `
                    <div class="card mb-4 shadow-sm">
                        <div class="card-header text-white bg-primary">
                            <h4 class="mb-0">${source}</h4>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled mb-0">
                `;
                    newsList.forEach(news => {
                        newsHtml += `
                        <li class="py-2 border-bottom">
                            <a href="${news.link}" target="_blank" class="text-dark text-decoration-none">
                                ${news.headline}
                            </a>
                        </li>
                    `;
                    });
                    newsHtml += `
                            </ul>
                        </div>
                    </div>
                `;
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
*/
// 當 DOM 完全加載後，初始化事件監聽器
document.addEventListener('DOMContentLoaded', function () {
    // 當表單提交時，觸發異步處理邏輯
    document.getElementById('prediction-form').onsubmit = async function (event) {
        event.preventDefault(); // 防止表單的默認提交行為，避免頁面重新加載

        // 顯示載入信息
        document.getElementById('loadingMessage').style.display = 'block'; // 顯示加載提示
        document.getElementById('result').innerHTML = '';  // 清除之前的結果
        document.getElementById('marquee').innerHTML = '正在分析中...';  // 設置跑馬燈的初始內容
        //document.getElementById('marquee').classList.add('marquee-animation'); // 開始跑馬燈動畫

        // 獲取表單數據
        const formData = new FormData(this);

        try {
            // 發送 /predict 請求
            const predictResponse = await fetch('/predict', { method: 'POST', body: formData });
            if (predictResponse.ok) {
                const { sentiment_mean, result, chart_filename, thirtydnews_response } = await predictResponse.json();
                document.getElementById('loadingMessage').style.display = 'none';

                // 顯示預測結果表格（行列顛倒）
                let table = `
        <table class="table table-bordered" style="width: 100%; table-layout: fixed;">
            <thead>
                <tr>
                    <th style="text-align: center;">看漲/看跌</th>
                    <th style="text-align: center;">日期</th>
                    <th style="text-align: center;">是否推薦買入</th>
                    <th style="text-align: center;">推薦持有時間</th>
                    <th style="text-align: center;">推薦賣出價格</th>
                    <th style="text-align: center;">止損策略</th>
                </tr>
            </thead>
            <tbody>
                <tr>
        `;

                for (let key in result) {
                    table += `<td style="text-align: center;">${result[key]}</td>`;
                }
                table += `</tr>`;
                table += `
            </tbody>
        </table>
        `;
                document.getElementById('dynamic-result').innerHTML = table;

                // Check if all conditions indicate no news data
                if (sentiment_mean === "No news data available." && 
                    chart_filename === "No chart available." && 
                    thirtydnews_response === "No news data available.") {
                    // Display "新聞資料不足"
                    document.getElementById('dynamic-container').innerHTML = '新聞資料不足';
                }else {
                    // Display sentiment mean
                    if (sentiment_mean === "No news data available.") {
                        document.getElementById('dynamic-sentiment-mean').innerHTML = '<p>新聞資料不足</p>';
                    } else if (sentiment_mean && sentiment_mean !== "No sentiment data available.") {
                        let sentimentMeanHTML = `
                        <div style="background-color: #f9f9f9; padding: 20px; border-radius: 50%; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); width: 250px; height: 250px; margin: 20px auto; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                            <h4 style="margin: 0;">平均分數</h4>
                            <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                                <p style="color: blue; font-weight: bold; font-size: 60px; margin: 0;">${sentiment_mean}</p>
                            </div>
                        </div>
                        `;
                        document.getElementById('dynamic-sentiment-mean').innerHTML = sentimentMeanHTML;
                    } else {
                        document.getElementById('dynamic-sentiment-mean').innerHTML = '<p>情緒平均分數未生成。</p>';
                    }

                    // Display sentiment trend chart
                    if (chart_filename === "No sentiment data for chart.") {
                        document.getElementById('dynamic-chart').innerHTML = '<p>沒有足夠情緒資料</p>';
                    } else if (chart_filename === "No chart available.") {
                        document.getElementById('dynamic-chart').innerHTML = '<p>繪製圖表失敗</p>';
                    } else if (chart_filename) {
                        let chartHTML = `
                        <div class="gemini-response-container">
                            <h4>趨勢圖</h4><iframe src="/static/chart/${chart_filename}" width="450px" height="300px"></iframe>
                        </div>`;
                        document.getElementById('dynamic-chart').innerHTML = chartHTML;
                    }

                    // Display Gemini 30-day news analysis
                    if (thirtydnews_response === "No news data available.") {
                        document.getElementById('dynamic-geminiResponse').innerHTML = '<p>新聞資料不足</p>';
                    } else if (thirtydnews_response && thirtydnews_response !== "exception") {
                        let geminiResponseHTML = `
                            <div class="gemini-response-container">
                                <h4>市場分析</h4>
                                <div class="gemini-answer">
                                    <pre>${thirtydnews_response}</pre>
                                </div>
                            </div>
                        `;
                        document.getElementById('dynamic-geminiResponse').innerHTML = geminiResponseHTML;
                    } else if (thirtydnews_response === "No data available.") {
                        document.getElementById('dynamic-geminiResponse').innerHTML = '<p>尚未生成或資源已耗盡。</p>';
                    }
                }


            } else {
                document.getElementById('loadingMessage').innerHTML = 'Error: 無法取得 predict 結果';
            }
        } catch (error) {
            console.error("Error:", error);
        }


        try {
            // 發送 /news 請求
            const newsResponse = await fetch('/news', { method: 'POST', body: formData });
            if (newsResponse.ok) {
                const newsData = await newsResponse.json();
                let newsHtml = '';


                // 動態生成新聞卡片
                for (const [source, newsList] of Object.entries(newsData)) {
                    newsHtml += `
                    <div class="card mb-4 shadow-sm">
                        <div class="card-header text-white bg-primary">
                            <h4 class="mb-0">${source}</h4>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled mb-0">
                    `;
                    newsList.forEach(news => {
                        newsHtml += `
                        <li class="py-2 border-bottom">
                            <a href="${news.link}" target="_blank" class="text-dark">
                                ${news.headline}
                            </a>
                        </li>
                    `;
                    });
                    newsHtml += `
                            </ul>
                        </div>
                    </div>
                    `;
                }
                document.getElementById('news-results').innerHTML = newsHtml;
            } else {
                console.error('找不到相關的新聞', newsResponse.statusText);
                document.getElementById('news-results').innerHTML = `
                <div class="alert alert-warning" role="alert">
                    找不到相關的新聞: ${newsResponse.statusText}
                </div>
                `;
            }
        } catch (error) {
            console.error('Error fetching /news:', error);
            document.getElementById('news-results').innerHTML = `
            <div class="alert alert-warning" role="alert">
                無法取得新聞數據。
            </div>
            `;
        }

        // 開始 SSE 實時更新
        const eventSource = new EventSource('/sse_stock_analysis');
        eventSource.onmessage = function (event) {
            const marquee = document.getElementById('marquee');
            marquee.innerHTML = event.data;
            //marquee.classList.add('marquee-animation');

            if (event.data === "分析完成!") {
                eventSource.close();
                //marquee.classList.remove('marquee-animation');
                marquee.innerHTML = "分析完成!";

                // Pause the video
                const video = document.getElementById('video');
                video.pause();

            }
        };
    };
});

// 控制影片播放的函數
function playVideo() {
    var video = document.getElementById("video");

    // 顯示影片並播放
    video.style.display = "block";  // 顯示影片
    video.play();                  // 播放影片
}

//刷新、清空內容
function clearContent() {
    // 清空區塊的內容
    document.getElementById("dynamic-result").innerHTML = "";
    document.getElementById("dynamic-sentiment-mean").innerHTML = "";
    // 清空 dynamic-container
    document.getElementById('dynamic-container').innerHTML = '';
    document.getElementById("dynamic-chart").innerHTML = "";
    document.getElementById("dynamic-geminiResponse").innerHTML = "";
    document.getElementById("news-results").innerHTML = "";
}