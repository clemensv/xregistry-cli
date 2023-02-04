using System.Threading.Tasks;
using Contoso.ERP.AzureFunction;
using CloudNative.CloudEvents;
using System;
using System.IO;

namespace function
{
    public class MyEventsDispatcher : IEventsDispatcher
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

        public Task OnEmployeeAddedAsync(CloudEvent cloudEvent, EmployeeData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnEmployeeDeletedAsync(CloudEvent cloudEvent, EmployeeDeletionData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnEmployeeUpdatedAsync(CloudEvent cloudEvent, EmployeeUpdatedData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnInventoryUpdatedAsync(CloudEvent cloudEvent, InventoryData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnPaymentsReceivedAsync(CloudEvent cloudEvent, PaymentData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnProductAddedAsync(CloudEvent cloudEvent, ProductData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnProductDeletedAsync(CloudEvent cloudEvent, ProductDeletionData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnProductUpdatedAsync(CloudEvent cloudEvent, ProductUpdatedData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnPurchaseOrderCreatedAsync(CloudEvent cloudEvent, PurchaseOrderData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnPurchaseOrderDeletedAsync(CloudEvent cloudEvent, object data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnPurchaseOrderUpdatedAsync(CloudEvent cloudEvent, PurchaseOrderUpdatedData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnReservationCancelledAsync(CloudEvent cloudEvent, CancellationData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnReservationPlacedAsync(CloudEvent cloudEvent, OrderData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnReservationRefundedAsync(CloudEvent cloudEvent, RefundData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnReturnRequestedAsync(CloudEvent cloudEvent, ReturnData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnShipmentAcceptedAsync(CloudEvent cloudEvent, ShipmentData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }

        public Task OnShipmentRejectedAsync(CloudEvent cloudEvent, ShipmentData data)
        {
            received.WriteLine(cloudEvent.Id);
            return Task.CompletedTask;
        }
    }
}
