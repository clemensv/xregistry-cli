// Instantiates the Consumer anmd Producer classes and calls their methods
// to send and receive messages.

using CloudNative.CloudEvents;
using CloudNative.CloudEvents.SystemTextJson;
using Contoso.ERP.Consumer;
using Contoso.ERP.Consumer.Contoso.ERP;
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

        JsonEventFormatter formatter = new JsonEventFormatter();
        var loggerFactory = LoggerFactory.Create(builder => builder.AddConsole());
        var logger = loggerFactory.CreateLogger("TestLogger");
        // Create a new instance of the Consumer class.

        var consumerPasswordCredential = new Contoso.ERP.Consumer.PlainEndpointCredential("test", "password");
        var consumer = EventsEventConsumer.CreateForMqttConsumer(logger, consumerPasswordCredential, new EventsEventDispatcher(unmatchedEvents));
        await consumer.StartAsync();

        var producerPasswordCredential = new Contoso.ERP.Producer.PlainEndpointCredential("test", "password");
        var producer = EventsEventProducer.CreateForMqttProducer(logger, producerPasswordCredential, ContentMode.Structured, formatter);
        producer.BeforeSend += (o, e) =>
        {
            if (e.Id == null) throw new ArgumentNullException();
            unmatchedEvents.Add(e.Id);
        };
        
        await producer.SendEmployeeAddedAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.EmployeeData()
        {
            EmployeeId = "123",
            Email = "johndoe@example.com",
            Department = "Sales",
            Name = "John Doe",
            Position = "Sales Manager"
        });
        await producer.SendEmployeeDeletedAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.EmployeeDeletionData()
        {
            EmployeeId = "123",
            Reason = "Termination"
        });
        await producer.SendEmployeeUpdatedAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.EmployeeUpdatedData()
        {
            EmployeeId = "123",
            Email = "johndoe@example.com",
            Department = "Sales",
            Name = "John Doe",
            Position = "Sales Manager"
        });
        await producer.SendInventoryUpdatedAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.InventoryData()
        {
            Location = "Musterstadt",
            ProductId = "abcdef",
            Quantity = 100
        });
        await producer.SendReservationCancelledAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.CancellationData()
        {
            OrderId = "2001272727",
            Reason = "Unknown",
            Status = "Cancelled"
        });
        await producer.SendReservationPlacedAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.OrderData()
        {
            CustomerId = "123",
            OrderId = "abc",
            Total = 1000,
            Items = new List<Contoso.ERP.Producer.Contoso.ERP.Events.OrderData.ItemsItem>()
            {
                new Contoso.ERP.Producer.Contoso.ERP.Events.OrderData.ItemsItem() {
                    ProductId = "123",
                    Price = 10,
                    Quantity = 5
                }
            }
        });
        await producer.SendReservationRefundedAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.RefundData()
        {
            OrderId = "123",
            Amount = 1000,
            Reason = "Unknown",
            Status = "Refunded"
        });
        await producer.SendProductAddedAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.ProductData()
        {
            ProductId = "124",
            Description = "Foo",
            Name = "Foo",
            Price = 123
        });
        await producer.SendProductDeletedAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.ProductDeletionData()
        {
            ProductId = "124",
            Reason = "Discontinued"
        });
        await producer.SendProductUpdatedAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.ProductUpdatedData()
        {
            ProductId = "124",
            Description = "Foo",
            Name = "Foo",
            Price = 123
        });
        await producer.SendPaymentsReceivedAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.PaymentData()
        {
            OrderId = "123",
            Paymentmethod = "Visa",
            Status = "Settled",
            Amount = 1000,
            TransactionId = "abc"
        });

        await Task.Delay(5000);

        await consumer.StopAsync();

        if (unmatchedEvents.Count != 0)
        {
            // we'll fail loudly if we didn't get all the events we sent
            throw new InvalidOperationException("Not all events were received");
        }
        return 0;
    }
}

internal class EventsEventDispatcher : Contoso.ERP.Consumer.Contoso.ERP.IEventsDispatcher
{
    private HashSet<string> unmatchedEvents;

    public EventsEventDispatcher(HashSet<string> unmatchedEvents)
    {
        this.unmatchedEvents = unmatchedEvents;
    }

    public Task OnEmployeeAddedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.EmployeeData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnEmployeeDeletedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.EmployeeDeletionData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnEmployeeUpdatedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.EmployeeUpdatedData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnInventoryUpdatedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.InventoryData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnPaymentsReceivedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.PaymentData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnProductAddedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.ProductData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnProductDeletedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.ProductDeletionData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnProductUpdatedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.ProductUpdatedData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnPurchaseOrderCreatedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.PurchaseOrderData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnPurchaseOrderDeletedAsync(CloudEvent cloudEvent, object? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;

    }

    public Task OnPurchaseOrderUpdatedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.PurchaseOrderUpdatedData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnReservationCancelledAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.CancellationData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnReservationPlacedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.OrderData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnReservationRefundedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.RefundData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnReturnRequestedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.ReturnData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnShipmentAcceptedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.ShipmentData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }

    public Task OnShipmentRejectedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.ShipmentData? data)
    {
        if (cloudEvent.Id != null)
            unmatchedEvents.Remove(cloudEvent.Id);
        return Task.CompletedTask;
    }
}