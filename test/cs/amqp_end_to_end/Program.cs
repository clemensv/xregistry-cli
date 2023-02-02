// Instantiates the Consumer anmd Producer classes and calls their methods
// to send and receive messages.

using CloudNative.CloudEvents;
using CloudNative.CloudEvents.Experimental.Endpoints;
using CloudNative.CloudEvents.SystemTextJson;
using Contoso.ERP.Consumer;
using Contoso.ERP.Producer;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading.Tasks;

public class Program
{
    public static async Task<int> Main(string[] args)
    {
        var blockingQueue = new BlockingCollection<byte[]>(new ConcurrentQueue<byte[]>());
        var unmatchedEvents = new HashSet<string>();

        AmqpProtocol.Initialize();

        JsonEventFormatter formatter = new JsonEventFormatter();
        var loggerFactory = LoggerFactory.Create(builder => builder.AddConsole());
        var logger = loggerFactory.CreateLogger("TestLogger");
        // Create a new instance of the Consumer class.

        var passwordCredential = new PlainEndpointCredential("test", "password");

        var consumer = EventsEventConsumer.CreateForAmqpConsumer(logger, passwordCredential, new EventsEventDispatcher(unmatchedEvents));
        await consumer.Endpoint.StartAsync();

        var producer = EventsEventProducer.CreateForAmqpProducer(logger, passwordCredential, ContentMode.Structured, formatter);
        producer.Endpoint.BeforeSend += (o, e) =>
        {
            if (e.Id == null) throw new ArgumentNullException();
            unmatchedEvents.Add(e.Id);
        };
        
        await producer.SendEmployeeAddedAsync(new Contoso.ERP.Producer.EmployeeData()
        {
            EmployeeId = "123",
            Email = "johndoe@example.com",
            Department = "Sales",
            Name = "John Doe",
            Position = "Sales Manager"
        });
        await producer.SendEmployeeDeletedAsync(new Contoso.ERP.Producer.EmployeeDeletionData()
        {
            EmployeeId = "123",
            Reason = "Termination"
        });
        await producer.SendEmployeeUpdatedAsync(new Contoso.ERP.Producer.EmployeeUpdatedData()
        {
            EmployeeId = "123",
            Email = "johndoe@example.com",
            Department = "Sales",
            Name = "John Doe",
            Position = "Sales Manager"
        });
        await producer.SendInventoryUpdatedAsync(new Contoso.ERP.Producer.InventoryData()
        {
            Location = "Musterstadt",
            ProductId = "abcdef",
            Quantity = 100
        });
        await producer.SendReservationCancelledAsync(new Contoso.ERP.Producer.CancellationData()
        {
            OrderId = "2001272727",
            Reason = "Unknown",
            Status = "Cancelled"
        });
        await producer.SendReservationPlacedAsync(new Contoso.ERP.Producer.OrderData()
        {
            CustomerId = "123",
            OrderId = "abc",
            Total = 1000,
            Items = new List<Contoso.ERP.Producer.OrderData.ItemsItem>()
            {
                new Contoso.ERP.Producer.OrderData.ItemsItem() {
                    ProductId = "123",
                    Price = 10,
                    Quantity = 5
                }
            }
        });
        await producer.SendReservationRefundedAsync(new Contoso.ERP.Producer.RefundData()
        {
            OrderId = "123",
            Amount = 1000,
            Reason = "Unknown",
            Status = "Refunded"
        });
        await producer.SendProductAddedAsync(new Contoso.ERP.Producer.ProductData()
        {
            ProductId = "124",
            Description = "Foo",
            Name = "Foo",
            Price = 123
        });
        await producer.SendProductDeletedAsync(new Contoso.ERP.Producer.ProductDeletionData()
        {
            ProductId = "124",
            Reason = "Discontinued"
        });
        await producer.SendProductUpdatedAsync(new Contoso.ERP.Producer.ProductUpdatedData()
        {
            ProductId = "124",
            Description = "Foo",
            Name = "Foo",
            Price = 123
        });
        await producer.SendPaymentsReceivedAsync(new Contoso.ERP.Producer.PaymentData()
        {
            OrderId = "123",
            Paymentmethod = "Visa",
            Status = "Settled",
            Amount = 1000,
            TransactionId = "abc"
        });

        await Task.Delay(5000);

        await consumer.Endpoint.StopAsync();

        if (unmatchedEvents.Count != 0)
        {
            // we'll fail loudly if we didn't get all the events we sent
            throw new InvalidOperationException("Not all events were received");
        }
        return 0;
    }
}

internal class EventsEventDispatcher : IEventsDispatcher
{
    private HashSet<string> unmatchedEvents;

    public EventsEventDispatcher(HashSet<string> unmatchedEvents)
    {
        this.unmatchedEvents = unmatchedEvents;
    }

    public Task OnEmployeeAddedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.EmployeeData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnEmployeeDeletedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.EmployeeDeletionData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnEmployeeUpdatedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.EmployeeUpdatedData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnInventoryUpdatedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.InventoryData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnPaymentsReceivedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.PaymentData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnProductAddedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.ProductData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnProductDeletedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.ProductDeletionData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnProductUpdatedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.ProductUpdatedData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnPurchaseOrderCreatedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.PurchaseOrderData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnPurchaseOrderDeletedAsync(CloudEvent cloudEvent, object data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;

    }

    public Task OnPurchaseOrderUpdatedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.PurchaseOrderUpdatedData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnReservationCancelledAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.CancellationData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnReservationPlacedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.OrderData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnReservationRefundedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.RefundData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnReturnRequestedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.ReturnData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnShipmentAcceptedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.ShipmentData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnShipmentRejectedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.ShipmentData data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }
}