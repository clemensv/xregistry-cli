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
        
        var consumer = EventsEventConsumer.CreateForHttpConsumer(logger, null, new EventsEventDispatcher(unmatchedEvents));
        await consumer.StartAsync();

        var producer = EventsEventProducer.CreateForHttpProducer(logger, null, ContentMode.Structured, formatter);
        producer.BeforeSend += (o, e) =>
        {
            if (e.Id == null) throw new ArgumentNullException();
            unmatchedEvents.Add(e.Id);
        };
        
        await producer.SendReservationCancelledAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.CancellationData()
        {
            OrderId = "2001272727",
            Reason = "Unknown",
            Status = "Cancelled"
        }, "application/protobuf");
        await producer.SendReservationPlacedAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.OrderData()
        {
            CustomerId = "123",
            OrderId = "abc",
            Total = 1000,
        }, "application/protobuf");
        await producer.SendPaymentsReceivedAsync(new Contoso.ERP.Producer.Contoso.ERP.Events.PaymentData()
        {
            OrderId = "123",
            Status = "Settled",
            Amount = 1000,
            TransactionId = "abc"
        }, "application/protobuf");

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

internal class EventsEventDispatcher : IEventsDispatcher
{
    private HashSet<string> unmatchedEvents;

    public EventsEventDispatcher(HashSet<string> unmatchedEvents)
    {
        this.unmatchedEvents = unmatchedEvents;
    }

    
    public Task OnPaymentsReceivedAsync(CloudEvent cloudEvent, Contoso.ERP.Consumer.Contoso.ERP.Events.PaymentData? data)
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
    
    
    public Task OnShipmentAcceptedAsync(CloudEvent cloudEvent,Contoso.ERP.Consumer.Contoso.ERP.Events.ShipmentData? data)
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