using System.Threading.Tasks;
using Contoso.ERP.AzureFunction;
using CloudNative.CloudEvents;
using System;
using System.IO;
using Contoso.ERP.AzureFunction.Contoso.ERP;

namespace function
{
    public class MyEventsDispatcher : Contoso.ERP.AzureFunction.Contoso.ERP.IEventsDispatcher
    {
        StreamWriter received; 

        public MyEventsDispatcher()
        {
            var receivedFile = System.Environment.GetEnvironmentVariable("RECEIVED_FILE") ?? "received.txt";
            received = new StreamWriter(receivedFile, new FileStreamOptions()
            {
                Mode = FileMode.Create,
                Access = FileAccess.Write 
            });
            received.AutoFlush = true;
        }

        ~MyEventsDispatcher()
        {
            received.Close();
        }

        public Task OnEmployeeAddedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.EmployeeData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnEmployeeDeletedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.EmployeeDeletionData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnEmployeeUpdatedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.EmployeeUpdatedData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnInventoryUpdatedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.InventoryData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnPaymentsReceivedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.PaymentData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnProductAddedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.ProductData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnProductDeletedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.ProductDeletionData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnProductUpdatedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.ProductUpdatedData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnPurchaseOrderCreatedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.PurchaseOrderData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnPurchaseOrderDeletedAsync(CloudEvent cloudEvent, object data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnPurchaseOrderUpdatedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.PurchaseOrderUpdatedData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnReservationCancelledAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.CancellationData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnReservationPlacedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.OrderData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnReservationRefundedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.RefundData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnReturnRequestedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.ReturnData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnShipmentAcceptedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.ShipmentData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnShipmentRejectedAsync(CloudEvent cloudEvent, Contoso.ERP.AzureFunction.Contoso.ERP.Events.ShipmentData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }
    }
}
