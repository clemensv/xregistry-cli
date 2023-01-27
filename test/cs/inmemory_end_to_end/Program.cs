// Instantiates the Consumer anmd Producer classes and calls their methods
// to send and receive messages.

using CloudNative.CloudEvents;
using CloudNative.CloudEvents.Experimental.Endpoints;
using CloudNative.CloudEvents.SystemTextJson;
using Contoso.ERP.Consumer.Contoso.ERP.Events;
using Contoso.ERP.Producer.Contoso.ERP.Events;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Console;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Net.Mime;
using System.Runtime.Serialization;
using System.Threading;
using System.Threading.Tasks;

public class Program
{
    public static async Task<int> Main(string[] args)
    {
        var blockingQueue = new BlockingCollection<byte[]>(new ConcurrentQueue<byte[]>());
        var unmatchedEvents = new HashSet<string>();


        JsonEventFormatter formatter = new JsonEventFormatter();
        var loggerFactory = LoggerFactory.Create(builder => builder.AddConsole());
        var logger = new TestLogger(loggerFactory.CreateLogger<Program>());

        // Create a new instance of the Consumer class.
        TestConsumerEndpoint consumerEndpoint = new TestConsumerEndpoint(unmatchedEvents, logger, blockingQueue);
        EventConsumer consumer = new EventConsumer(consumerEndpoint, ContentMode.Structured, formatter);
        TestProducerEndpoint producerEndpoint = new TestProducerEndpoint(unmatchedEvents, blockingQueue);
        EventProducer producer = new EventProducer(producerEndpoint, ContentMode.Structured, formatter);

        await consumerEndpoint.StartAsync();

        await producer.SendEmployeeAddedAsync(new Contoso.ERP.Producer.EmployeeData()).ConfigureAwait(false);
        await producer.SendEmployeeDeletedAsync(new Contoso.ERP.Producer.EmployeeDeletionData()).ConfigureAwait(false);
        await producer.SendEmployeeUpdatedAsync(new Contoso.ERP.Producer.EmployeeUpdatedData()).ConfigureAwait(false);
        await producer.SendInventoryUpdatedAsync(new Contoso.ERP.Producer.InventoryData()).ConfigureAwait(false);
        await producer.SendReservationCancelledAsync(new Contoso.ERP.Producer.CancellationData());
        await producer.SendReservationPlacedAsync(new Contoso.ERP.Producer.OrderData()).ConfigureAwait(false);
        await producer.SendReservationRefundedAsync(new Contoso.ERP.Producer.RefundData()).ConfigureAwait(false);
        await producer.SendProductAddedAsync(new Contoso.ERP.Producer.ProductData()).ConfigureAwait(false);
        await producer.SendProductDeletedAsync(new Contoso.ERP.Producer.ProductDeletionData()).ConfigureAwait(false);
        await producer.SendProductUpdatedAsync(new Contoso.ERP.Producer.ProductUpdatedData()).ConfigureAwait(false);
        await producer.SendPaymentsReceivedAsync(new Contoso.ERP.Producer.PaymentData()).ConfigureAwait(false);

        await Task.Delay(5000);
            
        await consumerEndpoint.StopAsync();

        if (unmatchedEvents.Count != 0 || logger.LoggedError )
        {
            // we'll fail loudly if we didn't get all the events we sent
            throw new InvalidOperationException("Not all events were received");
        }
        return 0;
    }
}

class TestLogger : ILogger
{
    public bool LoggedError { get; private set; }
    ILogger innerLogger;

    public TestLogger(ILogger innerLogger)
    {
        this.innerLogger = innerLogger;
    }
    
    public IDisposable? BeginScope<TState>(TState state) where TState : notnull
    {
        return innerLogger.BeginScope(state);
    }

    public bool IsEnabled(LogLevel logLevel)
    {
        return innerLogger.IsEnabled(logLevel);
    }

    public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
    {
        if (logLevel == LogLevel.Error)
        {
            LoggedError = true;
        }
        innerLogger.Log(logLevel, eventId, state, exception, formatter);
    }
}

class TestProducerEndpoint : ProducerEndpoint
{
    private readonly HashSet<string> sentEvents;
    private BlockingCollection<byte[]> blockingQueue;

    public TestProducerEndpoint(HashSet<string> sentEvents, BlockingCollection<byte[]> blockingQueue)
    {
        this.sentEvents = sentEvents;
        this.blockingQueue = blockingQueue;
    }

    public override Task SendAsync(CloudEvent cloudEvent, ContentMode contentMode, CloudEventFormatter formatter)
    {
        sentEvents.Add(cloudEvent.Id);
        blockingQueue.Add(formatter.EncodeStructuredModeMessage(cloudEvent, out var contentType).ToArray());
        return Task.CompletedTask;
    }
}

class TestConsumerEndpoint : ConsumerEndpoint
{
    private readonly HashSet<string> sentEvents;
    private readonly BlockingCollection<byte[]> blockingQueue;
    private CancellationTokenSource cts;
    JsonEventFormatter formatter = new JsonEventFormatter();
    Task loop = null;

    public TestConsumerEndpoint(HashSet<string> sentEvents, ILogger logger, BlockingCollection<byte[]> blockingQueue) :base(logger)
    {
        this.cts = new CancellationTokenSource();
        this.sentEvents = sentEvents;
        this.blockingQueue = blockingQueue;
    }
    
    public override Task StartAsync()
    {
        loop = Task.Run(() => {
            while (!cts.Token.IsCancellationRequested)
            {
                try
                {
                    // the encoding is guessed by content type so we will use Json here
                    var msg = blockingQueue.Take(cts.Token);
                    var cloudEvent = formatter.DecodeStructuredModeMessage(new ReadOnlyMemory<byte>(msg), new ContentType("application/cloudevents+json"), null);
                    sentEvents.Remove(cloudEvent.Id);
                    DeliverEvent(cloudEvent);
                }
                catch (OperationCanceledException)
                {
                    // we're done
                    break;
                }
            }
        });
        return Task.CompletedTask;
    }

    public override async Task StopAsync()
    {
        cts.Cancel();
        await loop;
    }
}