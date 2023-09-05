using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Net.Http;



namespace BlindSenseRegistry
{
    public partial class Form1 : Form
    {
        private string ApiUrl = "http://18.215.158.198:3011";
        public Form1()
        {
            InitializeComponent();
        }

        private async void submitBtn_Click(object sender, EventArgs e)
        {
            string name = Uri.EscapeDataString(txtClientName.Text);
            string contactName = Uri.EscapeDataString(txtContactName.Text);
            string contactPhone = Uri.EscapeDataString(txtPhoneNum.Text);
            string contactEmail = Uri.EscapeDataString(txtEmail.Text);
            string chipID = Uri.EscapeDataString(txtid.Text);

            using (HttpClient client = new HttpClient())
            {
                string apiUrl = $"{ApiUrl}/register?clientName={name}&contactName={contactName}&contactPhone={contactPhone}&contactEmail={contactEmail}&clientID={chipID}";
                HttpResponseMessage response = await client.PostAsync(apiUrl, null);

                if (response.IsSuccessStatusCode)
                {
                    MessageBox.Show("Data submitted successfully!");
                }
                else
                {
                    MessageBox.Show("Failed to submit data.");
                }
            }
        }
    }
}
