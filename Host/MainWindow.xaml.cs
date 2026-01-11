using System.Windows;
using Microsoft.Web.WebView2.Core; // Thêm dòng này

namespace Host
{
	public partial class MainWindow : Window
	{
		public MainWindow()
		{
			InitializeComponent();
			InitializeWebView(); // Gọi hàm khởi tạo
		}

		// Hàm async để khởi tạo môi trường trình duyệt
		private async void InitializeWebView()
		{
			try
			{
				// 1. Đảm bảo Core WebView2 đã sẵn sàng
				await webView.EnsureCoreWebView2Async(null);

				// 2. (Tùy chọn) Mở sẵn cửa sổ F12 DevTools để debug lỗi Web/JS
				// Rất tiện khi phát triển, sau này đóng gói thì xóa dòng này đi
				webView.CoreWebView2.OpenDevToolsWindow();
			}
			catch (Exception ex)
			{
				MessageBox.Show("Lỗi khởi tạo WebView2: " + ex.Message);
			}
		}
	}
}